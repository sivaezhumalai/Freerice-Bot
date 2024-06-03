import requests as r
import json
import logging

logging.basicConfig(level=logging.CRITICAL)

DEFAULT_TIMEOUT = 5

class Data:
    def __init__(self):
        self.error = False
        self.error_id = 0
        self.error_info = []

        self.game = ''
        self.name = ''
        self.rank = 0
        self.avtr = ''
        self.members = []
        self.rice_total = 0
        self.streak = 0
        self.question_id = ''
        self.question_txt = ''
        self.options = []

class Freerice:
    new_game_url = 'https://engine.freerice.com/games?lang=en'
    new_game_mth = 'POST'
    answer_url2 = '/answer?lang=en'
    answer_mth = 'PATCH'

    def __init__(self, user_id, timeout=DEFAULT_TIMEOUT):
        self.user = user_id
        self.game = ''
        self.n_games = 0
        self.init_level = 1
        self.timeout = timeout
        self.default_headers = {
            'Content-type': 'application/json',
            'Origin': 'https://freerice.com',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
            'Accept': 'application/vnd.api+json;version=2'
        }
        self.categories = {
            'multiplication-table': '66f2a9aa-bac2-5919-997d-2d17825c1837'
        }
        self.answer_url = ''

    def newGame(self):
        data = {
            'category': self.categories['multiplication-table'],
            'level': self.init_level,
            'user': self.user
        }

        req = r.request(
            self.new_game_mth,
            self.new_game_url,
            json=data,
            headers=self.default_headers,
            timeout=self.timeout
        )

        ret = Data()

        try:
            data = req.json()
        except json.JSONDecodeError:
            ret.error = True
            ret.error_id = 1
            ret.error_info = 'JSON decode error.'
            self.last_ret_v = ret
            return ret

        if 'errors' in data:
            ret.error = True
            ret.error_info = data['errors']
            self.last_ret_v = ret
            return ret

        self.answer_url = data['data']['links']['self']
        ret.game = data['data']['id']
        ret.question_id = data['data']['attributes']['question_id']
        ret.question_txt = data['data']['attributes']['question']['text']
        ret.options = data['data']['attributes']['question']['options']
        try:
            ret.rice_total = data['data']['attributes']['userattributes']['rice']
        except KeyError:
            ret.rice_total = data['data']['attributes']['user_rice_total']

        self.game = ret.game
        self.n_games += 1
        self.last_ret_v = ret
        return ret

    def submitAnswer(self, qId, answer_id):
        data = {
            'answer': answer_id,
            'question': qId,
            'user': self.user
        }

        url = self.answer_url + self.answer_url2

        req = r.request(
            self.answer_mth,
            url,
            json=data,
            headers=self.default_headers,
            timeout=self.timeout
        )

        ret = Data()

        try:
            data = req.json()
        except json.JSONDecodeError:
            ret.error = True
            ret.error_id = 1
            ret.error_info = 'JSON decode error.'
            self.last_ret_v = ret
            return ret

        if 'errors' in data:
            ret.error = True
            ret.error_info = data['errors']
            self.last_ret_v = ret
            return ret

        try:
            ret.game = data['data']['id']
            ret.question_id = data['data']['attributes']['question_id']
            ret.question_txt = data['data']['attributes']['question']['text']
        except:
            pass

        try:
            ret.streak = data['data']['attributes']['streak']
            try:
                ret.rice_total = data['data']['attributes']['userattributes']['rice']
            except KeyError:
                try:
                    ret.rice_total = data['data']['attributes']['user_rice_total']
                except KeyError:
                    ret.error_id = 2
                    ret.rice_total = 0
        except KeyError:
            ret.error = True

        self.last_ret_v = ret
        return ret

def main(user_id):
    fr = Freerice(user_id)

    while True:
        game_data = fr.newGame()

        if game_data.error:
            print("Error starting new game:", game_data.error_info)
            break

        print("New game started. Question:", game_data.question_txt)

        question_text = game_data.question_txt
        question_id = game_data.question_id

        # Assuming multiplication questions
        operands = question_text.split(' x ')
        if len(operands) != 2:
            print("Unexpected question format:", question_text)
            break

        try:
            answer = int(operands[0]) * int(operands[1])
        except ValueError:
            print("Failed to calculate the answer for:", question_text)
            break

        print(f"Calculated answer for '{question_text}' is {answer}")

        # Find the correct answer id
        answer_id = None
        for option in game_data.options:
            if option['text'] == str(answer):
                answer_id = option['id']
                break

        if not answer_id:
            print("Failed to find the correct answer id for:", answer)
            break

        result = fr.submitAnswer(question_id, answer_id)
        if result.error:
            print("Error submitting answer:", result.error_info)
            break

        print(f"Submitted answer. Streak: {result.streak}, Rice Total: {result.rice_total}")

if __name__ == "__main__":
    user_id = "6aaf625a-2252-4ca9-8edf-19041cee4b61"
    main(user_id)
