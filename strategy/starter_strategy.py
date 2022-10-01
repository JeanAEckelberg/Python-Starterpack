import itertools
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
        t1 = (0, 9)
        STARTS = [Position(xy[0], xy[1]) for xy in itertools.product(t1, t1)]
        t2 = (4, 5)
        HILLS = [Position(xy[0], xy[1]) for xy in itertools.product(t2, t2)]
        BOARD = [Position(x, y) for x in range(10) for y in range(10)]
        INACTIVE = [0, 0, 0, 0]

    class PlayerConstants:
        START_CLASS = game.character_class.CharacterClass.WIZARD
        ATTACK_DISTANCE = -1
        ATTACK_DAMAGE = -1
        SPAWN = Position(0, 0)
        SPEED = -1
        MY_PLAYER_STATE = game.player_state.PlayerState()


def check_player_activity(game_state: GameState):
    for i in range(4):
        if game_state.player_state_list[i].position in Constants.BoardConstants.STARTS:
            Constants.BoardConstants.INACTIVE[i] += 1
        else:
            Constants.BoardConstants.INACTIVE[i] = 0

def get_active_players() -> [int]:
    return list(filter(lambda p: Constants.BoardConstants.INACTIVE[p]<3, range(4)))
    # return [x for x, y in enumerate(Constants.BoardConstants.INACTIVE) if y < 3]


# returns all players that we can kill this turn
def get_killables(game_state: GameState, my_player_index: int, damage: int, check_shield: bool) -> [(int, game.player_state.PlayerState)]:
    my_location = game_state.player_state_list[my_player_index].position
    try:
        eligible = get_attackable(my_player_index, game_state)
        eligible = sorted(
            filter(lambda p: ((not check_shield) or (check_shield and p[1].item!=Item.SHIELD)) and p[1].health <= (4 if p[1].item == Item.PROCRUSTEAN_IRON else damage), map(lambda ip: (ip[0], ip[1], ip[1].health), eligible)),
            key=lambda tup: tup[2], reverse=True)
        return eligible
    except Exception as e:
        return []


# get the maximum range of the given player
# alex did this one he did he is very proud of it :)
def get_range(player: PlayerState) -> int:
    r = 0

    # check player class, assign proper inherent range for class
    temp = player.character_class.value
    if isinstance(temp, game.stat_set.StatSet):
        r = temp.range
    # add one to range if player has HUNTER SCOPE equipped
    if (player.item == Item.HUNTER_SCOPE):
        r += 1
    return r


def get_speed(player: PlayerState) -> int:
    speed = 0

    # check player class, assign proper inherent range for class
    temp = player.character_class.value
    if isinstance(temp, game.stat_set.StatSet):
        speed = temp.speed

    if ( player == Constants.PlayerConstants.MY_PLAYER_STATE ):
        speed //= 2
        speed *= 2

    if (player.item == Item.ANEMOI_WINGS):
        speed += 1
    if (player.item == Item.SPEED_POTION):
        speed += 2
    return speed


def get_damage(player: PlayerState) -> int:
    damage = 0

    # check player class, assign proper inherent damage for class
    temp = player.character_class.value
    if isinstance(temp, game.stat_set.StatSet):
        damage = temp.damage

    if (player.item == Item.RALLY_BANNER):
        damage += 2
    if (player.item == Item.STRENGTH_POTION):
        damage += 4

    return damage


# first item in the return is the range, second item in the return is the player index
def get_ranges(game_state: GameState) -> [(int, int)]:
    return [(get_range(game_state.player_state_list[p]), p) for p in range(4)]


# set up constants at the start of the game
def initialize(game_state: GameState, my_player_index: int) -> None:
    Constants.PlayerConstants.SPAWN = game_state.player_state_list[my_player_index].position


# gets all possible locations for a player to move to
def get_possible(player: PlayerState) -> [Position]:
    return list(filter(lambda pos: util.utility.manhattan_distance(player.position, pos) <= get_speed(player),
                       Constants.BoardConstants.BOARD))


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
        sorted(
            list(map(lambda hill: (util.utility.manhattan_distance(pos, hill), hill), Constants.BoardConstants.HILLS)),
            key=lambda tup: tup[0])[0][1]


# determines if two positions are the same positions
def same_pos(pos1: Position, pos2: Position) -> bool:
    return pos1.x == pos2.x and pos1.y == pos2.y


# returns all players that are within attack distance
def get_attackable(player_index: int, game_state: GameState) -> [(int, PlayerState)]:
    return list(filter(lambda ip: ip[0] != player_index and util.utility.chebyshev_distance(ip[1].position,
                                                                                            game_state.player_state_list[
                                                                                                player_index].position) <= get_range(
        game_state.player_state_list[player_index]), list(zip(range(4), game_state.player_state_list))))


# returns the possible damage to the passed hill tile
def hill_damage(enemy_poses: [(int, Position)], game_state: GameState, hill: Position) -> int:
    return sum([get_damage(game_state.player_state_list[player[0]]) for player in enemy_poses if
                get_range(game_state.player_state_list[player[0]]) >= util.utility.chebyshev_distance(player[1], hill)])


# returns a list of the possible damage on each hill tile
def get_hill_damages(enemy_poses: [(int, Position)], game_state: GameState) -> [(int, Position)]:
    return [(hill_damage(enemy_poses, game_state, hill), hill) for hill in Constants.BoardConstants.HILLS]


# assumes all players move towards the center and returns the new positions of the players
def predict(my_player_index: int, game_state: GameState) -> [(int, Position)]:
    return [(p_index, get_next_pos(game_state.player_state_list[p_index],
                                   closest_hill(game_state.player_state_list[p_index].position)))
            for p_index in range(4) if p_index != my_player_index]


# initialization for constants at the start of each turn
def initialize_turn(my_player_index: int, game_state: GameState) -> None:
    if game_state.turn == 1:
        initialize(game_state, my_player_index)

    Constants.PlayerConstants.MY_PLAYER_STATE = game_state.player_state_list[my_player_index]
    Constants.PlayerConstants.SPEED = get_speed(game_state.player_state_list[my_player_index])
    Constants.PlayerConstants.ATTACK_DISTANCE = get_range(game_state.player_state_list[my_player_index])
    Constants.PlayerConstants.ATTACK_DAMAGE = get_damage(game_state.player_state_list[my_player_index])


class StarterStrategy(Strategy):
    def strategy_initialize(self, my_player_index: int):
        return Constants.PlayerConstants.START_CLASS

    def move_action_decision(self, game_state: GameState, my_player_index: int) -> Position:
        current_location = game_state.player_state_list[my_player_index].position

        if game_state.player_state_list[my_player_index].gold >= 8 and \
                same_pos(current_location, Constants.PlayerConstants.SPAWN) and \
                game_state.player_state_list[my_player_index].item == Item.NONE:
            return current_location



        next_state_guess = predict(my_player_index, game_state)
        hill_damages = sorted(get_hill_damages(next_state_guess, game_state), key=lambda dh: dh[0])
        min_damage = hill_damages[0][0]
        best_hills = list(map(lambda dh: dh[1], list(filter(lambda dh: dh[0] == min_damage, hill_damages))))
        target = \
        sorted(list(map(lambda hill: (util.utility.manhattan_distance(hill, current_location), hill), best_hills)),
               key=lambda dh: dh[0])[0][1]
        next_pos = get_next_pos(Constants.PlayerConstants.MY_PLAYER_STATE, target)
        if len(get_active_players()) == 2:
            enemy = get_active_players()[int(get_active_players()[0]==my_player_index)]
            if get_range(game_state.player_state_list[enemy])<get_range(game_state.player_state_list[my_player_index]):
                enemyPos = get_next_pos(game_state.player_state_list[enemy], closest_hill(game_state.player_state_list[enemy].position))
                dist = util.utility.chebyschev_distance(enemyPos, next_pos)
                e = game_state.player_state_list[enemy]
                p = game_state.player_state_list[my_player_index]
                next_pos = sorted(list(map(lambda pos: (pos, 2*int(pos in Constants.BoardConstants.HILLS) + int(dist<=get_range(p)) + -2.5*int(dist<=get_range(e))), get_possible(p))), key=lambda pos: pos[1], reverse=True)[0]
        return next_pos

    def attack_action_decision(self, game_state: GameState, my_player_index: int) -> int:
        my_location = game_state.player_state_list[my_player_index].position
        try:
            eligible = get_killables(game_state, my_player_index, get_damage(game_state.player_state_list[my_player_index]), True)
            eligible = get_attackable(my_player_index, game_state) if len(eligible)==0 else eligible
            eligible = sorted(
                map(lambda ip: (ip[0], ip[1], ip[1].score), eligible), key = lambda tup: tup[2], reverse=True)
                # map(lambda ip: (ip[0], ip[1], util.utility.chebyshev_distance(my_location, ip[1].position)), eligible),
                # key=lambda tup: tup[2])

            # eligible = sorted(map(lambda ip: (ip[0], ip[1], ip[1].health), eligible), key=lambda tup: tup[2])

            return eligible[0][0]
        except Exception as e:
            return (my_player_index + 1) % 4

    def buy_action_decision(self, game_state: GameState, my_player_index: int) -> Item:
        if (game_state.player_state_list[my_player_index].gold >= 8) and same_pos(
            game_state.player_state_list[my_player_index].position, Constants.PlayerConstants.SPAWN) and (
                game_state.player_state_list[my_player_index].item == Item.NONE):
            scope_points = sum(list(map(lambda p: p.score, list(filter(
                lambda p: p.character_class == game.character_class.CharacterClass.KNIGHT
                          or p.character_class == game.character_class.CharacterClass.ARCHER,
                list(filter(lambda p: p != game_state.player_state_list[my_player_index], game_state.player_state_list)))))))
            banner_points = sum(list(map(lambda p: p.score, list(filter(
                lambda p: p.character_class == game.character_class.CharacterClass.WIZARD,
                list(filter(lambda p: p != game_state.player_state_list[my_player_index], (game_state.player_state_list))))))))
            return Item.HUNTER_SCOPE if scope_points >= banner_points else Item.RALLY_BANNER
        return Item.NONE
        #
        # return Item.HUNTER_SCOPE if (game_state.player_state_list[my_player_index].gold >= 8) and same_pos(
        #     game_state.player_state_list[my_player_index].position, Constants.PlayerConstants.SPAWN) and (
        #                                     game_state.player_state_list[
        #                                         my_player_index].item == Item.NONE) else Item.NONE

        # return Item.NONE


    def use_action_decision(self, game_state: GameState, my_player_index: int) -> bool:
        # this is the first phase to run, so initialize constants for the turn
        initialize_turn(my_player_index, game_state)
        check_player_activity(game_state)
        # [print(x) for x in get_active_players(game_state)]

        return False
