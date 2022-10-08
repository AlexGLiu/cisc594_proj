import numpy as np
import names
import random
from collections import OrderedDict, deque, defaultdict

class CustomError(Exception):
    """Base class for exceptions in this module."""
    pass

class CardNumberError(CustomError):
    def __init__(self, message, number):
        self.message = message
        self.number = number
    def __str__(self):
        return f"The numer {self.number} is {self.message} than the allowed card number range: 1~52."
class CardNumberDisaster(CustomError):
    def __init__(self,card):
        self.card = card
    def __str__(self):
        return f"The card numer {self.card.name()} is illegal."


# It is the card class, there are 52 cards in total, 13 cards for each suit.
# So that we use the id between 1 and 52 to initialize the card.
class Card:
    suit_map = {0: 'Heart',
                1: 'Diamond',
                2: 'Spade',
                3: 'Club'}

    def __init__(self, number, card_code=None):
        if number > 52:
            raise CardNumberError('larger', number)
        elif number < 1:
            raise CardNumberError('smaller', number)
        else:
            self.number = (number - 1) % 13 + 1  # it is the number of this card, no matter which suit, 1-13
            self.suit = Card.suit_map[(number - 1) // 13]  # it is the suit, one of the four
            self.card_id = number  # it is the id of the card, each card has an unique id, 1-52
            self.name = self.name()
            self.left = None
            self.right = None
            self.previous = None
            self.available = False
            self.suppressed = False
            self.player_id = None
            self.card_code = number if card_code is None else card_code
            self.onboard = False

    def __str__(self):
        return f"This card is {self.suit} {self.number}. The uid of this card is {self.card_id}."

    def name(self):
        return f"{self.suit} {self.number}"

    # if the card is to be used
    def issue(self):
        self.onboard = True
        self.available = False
        if self.left is not None:
            self.left.available = True
        if self.right is not None:
            self.right.available = True

    # if the card is to be suppressed
    def suppress(self):
        self.suppressed = True
        self.available = False


class Player:
    identity = 0  # it will be accumlated for each player

    def __init__(self, name=None, email=None):
        Player.identity += 1
        self.name = name or names.get_first_name()
        self.email = email
        self.player_id = Player.identity
        self.hand_card = None
        self.decoder = {}  # only the player himself/herself knows the code of his/her own cards
        self.available = []
        self.suppressed = {}  # easier for the player to show suppressed card by suits
        self.score = 0

    def send(self, text, round_count, game_id):
        if self.email is None:
            print(text)
        else:
            #           leave blank here, may or may not to be updated for email use
            print(text)

    def get_hand_cards(self, hand_card):
        for card in hand_card:
            card.player_id = self.player_id
            self.decoder[card.card_code] = card.card_id  # All the card are represented by card id in the backend
        self.hand_card = OrderedDict(sorted([(card.card_id, card) for card in hand_card]))

    def _check_available(self):
        self.available = []
        for card_id, card in self.hand_card.items():
            if card.available:
                self.available.append(card_id)

    def show_available(self):
        send_text = "You current available cards are:\n"
        for card_id in self.available:
            send_text += (f"{self.hand_card[card_id].name} is available, "
                          + f"use card code {self.hand_card[card_id].card_code} if you want to use.\n")
        return send_text

    # tell the player which cards are in hand, which are available or have to suppress
    def show_hand_cards(self):
        send_text = "You currently have:\n"
        suppress_text = "\nYou have to suppress: \n"
        hand_cards = defaultdict(list)
        suppressed_cards = defaultdict(list)
        for card_id in self.hand_card.keys():
            hand_cards[self.hand_card[card_id].suit].append(str(self.hand_card[card_id].number))
            suppress_text += (f"{self.hand_card[card_id].name} is in your hand, "
                              + f"use card code {self.hand_card[card_id].card_code} if you want to suppress. \n")
        for card_id in self.suppressed.keys():
            suppressed_cards[self.suppressed[card_id].suit].append(str(self.suppressed[card_id].number))
        for suit in hand_cards.keys():
            send_text += f"{suit} {', '.join(hand_cards[suit])}.\n"
        send_text += '\nYou have suppressed: \n'
        for suit in suppressed_cards.keys():
            send_text += f"{suit} {', '.join(suppressed_cards[suit])}.\n"
        if len(self.available) == 0:  # only if there is no card available, player is allowed to suppress card
            send_text += suppress_text
        return send_text

    def issue(self, card_id):
        self._check_available()
        if len(self.available) == 0:
            print("There is no card available, please suppress one instead.")
            return False
        elif card_id in self.available:
            issued_card = self.hand_card.pop(card_id)
            issued_card.issue()
            return True
        elif card_id in self.hand_card.keys():
            print("This card is not available, please try again.")
            return False
        elif card_id < 1 or card_id > 52:
            print("Not a valid card id, please try again.")
            return False
        else:
            print('Not in your hand, please try again.')
            return False

    def suppress(self, card_id):
        self._check_available()
        if len(self.available) > 0:
            print("You have at least one card available, you need to issue one card.")
            return False
        elif card_id in self.available:
            print("This card is available, you need to issue one card.")
            return False
        elif card_id not in self.hand_card.keys():
            print("You don't have this card, please choose another one.")
            return False
        elif card_id in list(self.hand_card.keys()):
            suppressed_card = self.hand_card.pop(card_id)
            suppressed_card.suppress()
            self.suppressed[card_id] = suppressed_card
            self.score += suppressed_card.number
            return True
        else:
            print("Try again!")
            return False

    # The general action method for players. It will choose the detailed action (issue or suppress) based on
    # whether there is any card available on hand
    def action(self, round_count, game_id):
        self._check_available()
        if len(self.available) > 0:
            send_text = self.show_hand_cards() + '\n' + self.show_available()
            self.send(send_text, round_count, game_id)
            card_code = input("Please input the card code you want to issue: ")
            try:
                card_code = int(card_code)
                card_id = self.decoder[card_code]
            except:
                card_id = 0
            return self.issue(card_id)
        elif len(self.hand_card) > 0:
            send_text = self.show_hand_cards()
            self.send(send_text, round_count, game_id)
            card_code = input("Please input the card code you want to suppress: ")
            try:
                card_code = int(card_code)
                card_id = self.decoder[card_code]
            except:
                card_id = 0
            return self.suppress(card_id)
        else:
            print("You have no card left, pass.")
            return True


class Game:
    identity = 0

    def __init__(self, random_seed=123):
        Game.identity += 1
        self.game_id = Game.identity
        self.card_map = OrderedDict()  # all the calculation in the backend uses the id (card or player),
        self.player_map = OrderedDict()  # need to use this map to link the id to the object
        self.card_pool = []
        self.players = deque([])  # Here the deque is being used, because the player with Spade 7 need to start,
        # NOT based on the order of geting card
        pool = list(range(1, 53))
        random.seed(random_seed)
        random.shuffle(pool)
        self.onboard_cards = []  # record the cards on board
        self.min_score = 9999  # after the last round, the player has the lowest score wins
        self.winner = None
        self.encoder = {}  # create the visiable code for each card, it is different from the card id,
        # since we do not want the other players know which card is suppressed.
        # It is different in different game.
        for i, v in enumerate(pool):
            self.encoder[i + 1] = v

    def get_cards(self):
        previous_card = None
        """
        left means the card which number is -1 of current one, right means +1 of current card.
        However, for card.number < 7, +1 card is the previous card of current one, means if the previous card is not on the board, 
        the current one cannot be available. Since the +1 card already stored as the previous card, no need to set the right card.
        The same for card > 7, no need to set .left.
        """
        for i in range(1, 53):
            this_card = Card(i, self.encoder[i])
            if this_card.number < 7:
                this_card.left = previous_card  # left means the card which number is one less than the current one
                if previous_card is not None:
                    previous_card.previous = this_card  # previous card means, if previous one is not on the board,
                    # this card cannot be used
            elif this_card.number > 7:
                this_card.previous = previous_card  # 7 is the previous for both 6 and 8, here sets 8's.
                if previous_card is not None:
                    previous_card.right = this_card
            elif this_card.number == 7:  # For all suits, 7 is always be available, and it is the previous for both 6 and 8,
                # here sets 6's.
                this_card.left = previous_card
                previous_card.previous = this_card
                this_card.available = True  # set 7 to available

            else:
                raise CardNumberDisaster(this_card)  # not going to happen
            if this_card.number == 13:
                previous_card = None
            else:
                previous_card = this_card
            self.card_map[this_card.card_id] = this_card
        self.card_pool = list(self.card_map.values())  # list of card class objs
        random.shuffle(self.card_pool)

    def prepare(self):
        for i in range(4):  # make sure only four players
            this_name = input("Please input your name: ")
            this_name = None if this_name == '' else this_name
            this_email = input("Please input your email: ")
            this_email = None if this_email == '' else this_email
            this_player = Player(this_name, this_email)
            print(f"Welcome {this_player.name}, have fun!")
            this_player.get_hand_cards(self.card_pool[i * 13:(i + 1) * 13])
            self.player_map[this_player.player_id] = this_player
            self.players.append(this_player)  # Here the players are added to the deque one by one

        init_player = self.player_map[self.card_map[33].player_id]  # The one has Spade 7 need to be the first player
        first_player_index = self.players.index(init_player)
        # Here the new order is rotated, the same order as assigning cards, but the first player has the Spade 7
        self.players.rotate(-1 * first_player_index)

    def check_onboard(self, show=True):
        self.onboard_cards = []
        for card_id in self.card_map.keys():
            if self.card_map[card_id].onboard:
                self.onboard_cards.append(self.card_map[card_id])
        if show:
            current_onboard = defaultdict(list)
            for card in self.onboard_cards:
                current_onboard[card.suit].append(str(card.number))
            print("\nCurrent onboard cards are:")
            print("************************************************")
            for suit in current_onboard.keys():
                print(f"{suit} {', '.join(current_onboard[suit])}.")
            print("************************************************")

    def one_round(self, round_count, game_id, show=True):
        for player in self.players:
            self.check_onboard(show)
            print(f"\nIt is {player.name}'s turn.\n")
            while True:
                action_result = player.action(round_count, game_id)
                if action_result:
                    break

    def on_going(self):
        round_count = 0
        while round_count < 13:
            self.one_round(round_count, self.game_id)
            round_count += 1
        # After all rounds, check the result
        for player in self.players:
            print(f"{player.name} has {player.score} points.")
            if player.score < self.min_score:
                self.min_score = player.score
                self.winner = player
        print(f"{self.winner.name} wins!")