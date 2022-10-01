from random import Random
from game.game_state import GameState
import game.character_class
import util.utility
import game.stat_set
import game.player_state

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


def get_killables(game_state: GameState, my_player_index: int, damage: int) -> [(int, game.player_state.PlayerState)]:
    my_location = game_state.player_state_list[my_player_index].position
    try:
        eligible = get_attackable(my_player_index, my_location, game_state)
        eligible = sorted(filter(lambda p: p[1].health<=damage, map(lambda ip: (ip[0], ip[1], ip[1].health), eligible)), key=lambda tup: tup[2], reverse=True)
        return eligible
    except:
        return (my_player_index + 1) % 4


def initialize(game_state: GameState, my_player_index: int) -> None:
    Constants.PlayerConstants.SPAWN = game_state.player_state_list[my_player_index].position


def get_possible(current_location: Position) -> [Position]:
    return list(filter(lambda pos: util.utility.manhattan_distance(current_location, pos) <= Constants.PlayerConstants.SPEED, [Position(x, y) for x in range(10) for y in range(10)]))


def get_next_pos(possible_poses: [Position], target: Position) -> Position:
    return sorted(list(map(lambda pos: (pos, util.utility.chebyshev_distance(pos, target)), possible_poses)), key=lambda pd: pd[1])[0][0]


def closest_hill(current_pos: Position) -> Position:
    return sorted(list(map(lambda hill: (util.utility.manhattan_distance(current_pos, hill), hill), Constants.BoardConstants.HILLS)), key=lambda tup: tup[0])[0][1]


def same_pos(pos1: Position, pos2: Position) -> bool:
    return pos1.x == pos2.x and pos1.y == pos2.y


def get_attackable(my_player_index: int, my_location: Position, game_state: GameState) -> [(int, game.player_state.PlayerState)]:
    return list(filter(lambda ip: ip[0] != my_player_index and util.utility.chebyshev_distance(ip[1].position, my_location) <= Constants.PlayerConstants.ATTACK_DISTANCE, list(zip([0, 1, 2, 3], game_state.player_state_list))))


class StarterStrategy(Strategy):
    def strategy_initialize(self, my_player_index: int):
        return Constants.PlayerConstants.START_CLASS

    def move_action_decision(self, game_state: GameState, my_player_index: int) -> Position:
        current_location = game_state.player_state_list[my_player_index].position
        # step 1: map the distances to each hill -> [(dist, hill position)]
        # step 2: sort based on the distance
        # step 3: pick the hill position from the first element in the list
        if game_state.player_state_list[my_player_index].gold >= 8 and same_pos(current_location, Constants.PlayerConstants.SPAWN) and game_state.player_state_list[my_player_index].item == Item.NONE:
            return current_location
        possible_poses = get_possible(current_location)
        next_pos = get_next_pos(possible_poses, closest_hill(current_location))
        return next_pos


    def attack_action_decision(self, game_state: GameState, my_player_index: int) -> int:
        my_location = game_state.player_state_list[my_player_index].position
        # step 1: zip indexes over the players in the player_state_list -> [(index, player_state)]
        # step 2: filter out players that aren't eligible to attack
        # step 3: take the first player which is eligible to attack and return their index
        # if there are no eligible players, just return next index
        try:
            eligible = get_attackable(my_player_index, my_location, game_state)
            eligible = sorted(map(lambda ip: (ip[0], ip[1], util.utility.chebyshev_distance(my_location, ip[1].position)), eligible), key=lambda tup: tup[2])
            # eligible = sorted(map(lambda ip: (ip[0], ip[1], ip[1].health), eligible), key=lambda tup: tup[2])

            return eligible[0][0]
        except:
            return (my_player_index + 1) % 4

    def buy_action_decision(self, game_state: GameState, my_player_index: int) -> Item:

        if (game_state.player_state_list[my_player_index].gold >= 8) and same_pos(game_state.player_state_list[my_player_index].position, Constants.PlayerConstants.SPAWN) and (game_state.player_state_list[my_player_index].item == Item.NONE):
            return Item.HUNTER_SCOPE

        # if (game_state.player_state_list[my_player_index].gold >= 5) and same_pos(game_state.player_state_list[my_player_index].position, Constants.PlayerConstants.SPAWN) and (game_state.player_state_list[my_player_index].item == Item.NONE):
        #     return Item.STRENGTH_POTION

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

        if ( game_state.player_state_list[my_player_index].item == Item.ANEMOI_WINGS ):
            Constants.PlayerConstants.SPEED += 1
        elif ( game_state.player_state_list[my_player_index].item == Item.HUNTER_SCOPE ):
            Constants.PlayerConstants.ATTACK_DISTANCE += 1
        elif (game_state.player_state_list[my_player_index].item == Item.RALLY_BANNER):
            Constants.PlayerConstants.ATTACK_DAMAGE += 2

        # return game_state.player_state_list[my_player_index].item == Item.STRENGTH_POTION and get_attackable(my_player_index, game_state.player_state_list[my_player_index].position, game_state)
        return False