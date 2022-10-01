from random import Random
from game.game_state import GameState
import game.character_class
import util.utility
import game.stat_set
from game.player_state import PlayerState

from game.item import Item

from game.position import Position
from strategy.strategy import Strategy


class Constants:
    class BoardConstants:
        STARTS = [Position(0, 0), Position(0, 9), Position(9, 0), Position(9, 9)]
        HILLS = [Position(4, 4), Position(4, 5), Position(5, 4), Position(5, 5)]

    class PlayerConstants:
        START_CLASS = game.character_class.CharacterClass.KNIGHT
        ATTACK_DISTANCE = -1
        ATTACK_DAMAGE = -1
        SPAWN = Position(0, 0)
        SPEED = -1


# returns all players that we can kill this turn
def get_killables(game_state: GameState, my_player_index: int, damage: int) -> [(int, game.player_state.PlayerState)]:
    my_location = game_state.player_state_list[my_player_index].position
    try:
        eligible = get_attackable(my_player_index, game_state)
        eligible = sorted(
            filter(lambda p: p[1].health <= damage, map(lambda ip: (ip[0], ip[1], ip[1].health), eligible)),
            key=lambda tup: tup[2], reverse=True)
        return eligible
    except:
        return (my_player_index + 1) % 4


# get the maximum range of the given player
# alex did this one he did he is very proud of it :)
def get_range(player: PlayerState) -> int:
    r = 0

    # check player class, assign proper inherent range for class
    if (player.character_class == game.character_class.CharacterClass.KNIGHT):
        r = 1
    elif (player.character_class == game.character_class.CharacterClass.WIZARD):
        r = 2
    elif (player.character_class == game.character_class.CharacterClass.ARCHER):
        r = 3
    # add one to range if player has HUNTER SCOPE equipped
    if (player.item == Item.HUNTER_SCOPE):
        r += 1
    return r


def get_speed(player: game.player_state.PlayerState) -> int:
    speed = 0

    # check player class, assign proper inherent range for class
    if (player.character_class == game.character_class.CharacterClass.KNIGHT):
        speed = 2
    elif (player.character_class == game.character_class.CharacterClass.WIZARD):
        speed = 3
    elif (player.character_class == game.character_class.CharacterClass.ARCHER):
        speed = 4
    # add one to range if p     layer has HUNTER SCOPE equipped
    if (player.item == Item.ANEMOI_WINGS):
        speed += 2
    return speed


def get_damage(player: PlayerState) -> int:
    damage = 0

    # check player class, assign proper inherent damage for class
    if (player.character_class == game.character_class.CharacterClass.KNIGHT):
        damage = 6
    elif (player.character_class == game.character_class.CharacterClass.WIZARD):
        damage = 4
    elif (player.character_class == game.character_class.CharacterClass.ARCHER):
        damage = 2

    if (player.item == Item.RALLY_BANNER):
        damage += 2
    if (player.item == Item.STRENGTH_POTION):
        damage += 4

    return damage


# first item in the return is the range, second item in the return is the player index
def get_ranges(game_state: GameState) -> [(int, int)]:
    return [(get_range(game_state.player_state_list[p]), p) for p in [0, 1, 2, 3]]


def initialize(game_state: GameState, my_player_index: int) -> None:
    Constants.PlayerConstants.SPAWN = game_state.player_state_list[my_player_index].position


# gets all possible locations for a player to move to
def get_possible(player: PlayerState) -> [Position]:
    return list(filter(lambda pos: util.utility.manhattan_distance(player.position, pos) <= get_speed(player),
                       [Position(x, y) for x in range(10) for y in range(10)]))


# finds the next position for a player to move to based on the target Position
def get_next_pos(player: PlayerState, target: Position) -> Position:
    return sorted(list(map(lambda pos: (pos, util.utility.chebyshev_distance(pos, target)), get_possible(player))),
                  key=lambda pd: pd[1])[0][0]


# finds all hills that are within movement range of the given player
def hills_in_range(player: PlayerState) -> [Position]:
    return [hill for hill in Constants.BoardConstants.HILLS if
            util.utility.manhattan_distance(hill, player.position) <= get_speed(player)]


# finds the closest hill to the position
def closest_hill(pos: Position) -> Position:
    return \
    sorted(list(map(lambda hill: (util.utility.manhattan_distance(pos, hill), hill), Constants.BoardConstants.HILLS)),
           key=lambda tup: tup[0])[0][1]


# determines if two positions are the same positions
def same_pos(pos1: Position, pos2: Position) -> bool:
    return pos1.x == pos2.x and pos1.y == pos2.y


# returns all players that are within attack distance
def get_attackable(player_index: int, game_state: GameState) -> [(int, PlayerState)]:
    return list(filter(lambda ip: ip[0] != player_index and util.utility.chebyshev_distance(ip[1].position,
                                                                                            game_state.player_state_list[
                                                                                                player_index].position) <= get_range(
        game_state.player_state_list[player_index]), list(zip([0, 1, 2, 3], game_state.player_state_list))))


# returns the possible damage to the passed hill tile
def hill_damage(my_player_index: int, game_state: GameState, hill: Position) -> int:
    return sum([get_damage(game_state.player_state_list[player]) for player in [0, 1, 2, 3] if
         player != my_player_index and get_range(game_state.player_state_list[player]) >= util.utility.chebyshev_distance(
             game_state.player_state_list[player].position, hill)])


# returns a list of the possible damage on each hill tile
def get_hill_damages(my_player_index: int, game_state: GameState) -> [(int, Position)]:
    return [(hill_damage(my_player_index, game_state, hill), hill) for hill in Constants.BoardConstants.HILLS]


class StarterStrategy(Strategy):
    def strategy_initialize(self, my_player_index: int):
        return Constants.PlayerConstants.START_CLASS

    def move_action_decision(self, game_state: GameState, my_player_index: int) -> Position:
        current_location = game_state.player_state_list[my_player_index].position
        # step 1: map the distances to each hill -> [(dist, hill position)]
        # step 2: sort based on the distance
        # step 3: pick the hill position from the first element in the list
        if game_state.player_state_list[my_player_index].gold >= 8 and same_pos(current_location,
                                                                                Constants.PlayerConstants.SPAWN) and \
                game_state.player_state_list[my_player_index].item == Item.NONE:
            return current_location
        hill_damages = sorted(get_hill_damages(my_player_index, game_state), key=lambda dh: dh[0])
        min_damage = hill_damages[0][0]
        best_hills = list(map(lambda dh: dh[1], list(filter(lambda dh: dh[0] == min_damage, hill_damages))))
        target = sorted(list(map(lambda hill: (util.utility.manhattan_distance(hill, current_location), hill), best_hills)), key=lambda dh: dh[0])[0][1]
        next_pos = get_next_pos(game_state.player_state_list[my_player_index], target)
        return next_pos

    def attack_action_decision(self, game_state: GameState, my_player_index: int) -> int:
        my_location = game_state.player_state_list[my_player_index].position
        # step 1: zip indexes over the players in the player_state_list -> [(index, player_state)]
        # step 2: filter out players that aren't eligible to attack
        # step 3: take the first player which is eligible to attack and return their index
        # if there are no eligible players, just return next index
        try:
            eligible = get_attackable(my_player_index, game_state)
            eligible = sorted(
                map(lambda ip: (ip[0], ip[1], util.utility.chebyshev_distance(my_location, ip[1].position)), eligible),
                key=lambda tup: tup[2])
            # eligible = sorted(map(lambda ip: (ip[0], ip[1], ip[1].health), eligible), key=lambda tup: tup[2])

            return eligible[0][0]
        except:
            return (my_player_index + 1) % 4

    def buy_action_decision(self, game_state: GameState, my_player_index: int) -> Item:
        if (game_state.player_state_list[my_player_index].gold >= 8) and same_pos(
                game_state.player_state_list[my_player_index].position, Constants.PlayerConstants.SPAWN) and (
                game_state.player_state_list[my_player_index].item == Item.NONE):
            return Item.HUNTER_SCOPE
        return Item.NONE

    def use_action_decision(self, game_state: GameState, my_player_index: int) -> bool:
        # this is the first phase to ever run, so we do some initialization stuff if it's the first turn
        if game_state.turn == 1:
            initialize(game_state, my_player_index)
        my_class = game_state.player_state_list[my_player_index].character_class
        if (my_class == game.character_class.CharacterClass.KNIGHT):
            Constants.PlayerConstants.SPEED = 2
            Constants.PlayerConstants.ATTACK_DISTANCE = 1
            Constants.PlayerConstants.ATTACK_DAMAGE = 6
        elif (my_class == game.character_class.CharacterClass.WIZARD):
            Constants.PlayerConstants.SPEED = 3
            Constants.PlayerConstants.ATTACK_DISTANCE = 2
            Constants.PlayerConstants.ATTACK_DAMAGE = 4
        elif (my_class == game.character_class.CharacterClass.ARCHER):
            Constants.PlayerConstants.SPEED = 4
            Constants.PlayerConstants.ATTACK_DISTANCE = 3
            Constants.PlayerConstants.ATTACK_DAMAGE = 2

        if (game_state.player_state_list[my_player_index].item == Item.ANEMOI_WINGS):
            Constants.PlayerConstants.SPEED += 2
        elif (game_state.player_state_list[my_player_index].item == Item.HUNTER_SCOPE):
            Constants.PlayerConstants.ATTACK_DISTANCE += 1
        elif (game_state.player_state_list[my_player_index].item == Item.RALLY_BANNER):
            Constants.PlayerConstants.ATTACK_DAMAGE += 2

        return False