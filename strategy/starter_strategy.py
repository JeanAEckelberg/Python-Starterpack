from random import Random
from game.game_state import GameState
import game.character_class
import util.utility

from game.item import Item

from game.position import Position
from strategy.strategy import Strategy


class Constants:
    class BoardConstants:
        STARTS = [Position(0, 0), Position(0, 9), Position(9, 0), Position(9, 9)]
        HILLS = [Position(4, 4), Position(4, 5), Position(5, 4), Position(5, 5)]

    class PlayerConstants:
        START_CLASS = game.character_class.CharacterClass.KNIGHT
        ATTACK_DISTANCE = 2
        SPAWN = Position(0, 0)


def initialize(game_state: GameState, my_player_index: int) -> None:
    Constants.PlayerConstants.SPAWN = game_state.player_state_list[my_player_index].position


class StarterStrategy(Strategy):
    def strategy_initialize(self, my_player_index: int):
        return Constants.PlayerConstants.START_CLASS

    def move_action_decision(self, game_state: GameState, my_player_index: int) -> Position:
        current_location = game_state.player_state_list[my_player_index].position
        # step 1: map the distances to each hill -> [(dist, hill position)]
        # step 2: sort based on the distance
        # step 3: pick the hill position from the first element in the list
        return sorted(list(map(lambda hill: (util.utility.chebyshev_distance(current_location, hill), hill), Constants.BoardConstants.HILLS)), key=lambda tup: tup[0])[0][1]
        # return Position(5, 5)

    def attack_action_decision(self, game_state: GameState, my_player_index: int) -> int:
        # return Random().randint(0, 3)
        my_location = game_state.player_state_list[my_player_index].position
        # step 1: zip indexes over the players in the player_state_list -> [(index, player_state)]
        # step 2: filter out players that aren't eligible to attack
        # step 3: take the first player which is eligible to attack and return their index
        # if there are no eligible players, just return 0
        try:
            eligible = list(filter(lambda ip: ip[0] != my_player_index and util.utility.chebyshev_distance(ip[1].position, my_location) < PlayerConstants.ATTACK_DISTANCE, list(zip([0, 1, 2, 3], game_state.player_state_list))))
            eligible = sorted(map(lambda ip: (ip[0], ip[1], util.utility.chebyshev_distance(my_location, ip[1].position)), eligible), key=lambda tup: tup[2])
            return eligible[0][0]
        except:
            return (my_player_index + 1) % 4

    def buy_action_decision(self, game_state: GameState, my_player_index: int) -> Item:
        return Item.NONE

    def use_action_decision(self, game_state: GameState, my_player_index: int) -> bool:
        # this is the first phase to ever run, so we do some initialization shit if it's the first turn
        if game_state.turn == 1:
            initialize(game_state, my_player_index)
        return True
