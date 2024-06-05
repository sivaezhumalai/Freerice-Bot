import requests
import logging
import time

try:
    from torpy.http.requests import TorRequests
    torpy_installed = True
except ImportError:
    torpy_installed = False

logging.basicConfig(level=logging.INFO)

class Data:
    def __init__(self):
        self.error = False
        self.error_info = None
        self.game_id = None
        self.question_id = None
        self.question_txt = None
        self.answers = None
        self.rice_total = None
        self.streak = None
        self.rice_total_all = None
        self.rank = None
        self.name = None
        self.avtr = None

class Freerice:
    base_url = "https://engine.freerice.com"
    base_urls = {
        "game": f"{base_url}/gametoken",
        "answer": f"{base_url}/question",
        "profile": f"{base_url}/profile",
        "group": f"{base_url}/group"
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Freerice Bot"
    }
    tor = False
    num_hops = 3

    def __init__(self, user_id=None):
        self.user_id = user_id
        self.game_id = None
        self.num_games = 1
        self.timeout = 60

        if not torpy_installed:
            print("To use Tor, install torpy library with `pip install torpy`")
        
        self.session = requests.Session()

    def request(self, method, url, **kwargs):
        if self.tor:
            with TorRequests() as tor_requests:
                with tor_requests.get_session(hops_count=self.num_hops) as tor_session:
                    return tor_session.request(method, url, **kwargs)
        else:
            return self.session.request(method, url, **kwargs)

    def newGame(self):
        data = Data()
        url = f"{self.base_urls['game']}/new"
        payload = {
            "userId": self.user_id,
            "category": "english_vocabulary"
        }
        try:
            response = self.request("POST", url, json=payload, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            response_data = response.json()
            data.game_id = response_data["gameToken"]["gameId"]
            data.question_id = response_data["question"]["id"]
            data.question_txt = response_data["question"]["questionText"]
            data.answers = response_data["question"]["answers"]
            data.rice_total = response_data["userStats"]["riceTotal"]
        except requests.exceptions.RequestException as e:
            data.error = True
            data.error_info = str(e)
        except (ValueError, KeyError) as e:
            data.error = True
            data.error_info = f"JSON parsing error or key error: {str(e)}"
        return data

    def submitAnswer(self, question_id, answer):
        data = Data()
        url = f"{self.base_urls['answer']}/{question_id}"
        payload = {
            "answer": answer,
            "userId": self.user_id,
            "gameToken": self.game_id
        }
        try:
            response = self.request("PATCH", url, json=payload, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            response_data = response.json()
            data.streak = response_data["game"]["streak"]
            data.rice_total = response_data["game"]["riceTotal"]
            data.question_id = response_data["question"]["id"]
            data.question_txt = response_data["question"]["questionText"]
            data.answers = response_data["question"]["answers"]
        except requests.exceptions.RequestException as e:
            data.error = True
            data.error_info = str(e)
        except (ValueError, KeyError) as e:
            data.error = True
            data.error_info = f"JSON parsing error or key error: {str(e)}"
        return data

    def getUserStats(self, user=None, group=None):
        data = Data()
        if user:
            url = f"{self.base_urls['profile']}/{user}/totals"
        elif group:
            url = f"{self.base_urls['group']}/{group}/totals"
        else:
            data.error = True
            data.error_info = "No user or group specified"
            return data
        try:
            response = self.request("GET", url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            response_data = response.json()
            data.rice_total_all = response_data["riceTotal"]
            data.rank = response_data["rank"]
        except requests.exceptions.RequestException as e:
            data.error = True
            data.error_info = str(e)
        except (ValueError, KeyError) as e:
            data.error = True
            data.error_info = f"JSON parsing error or key error: {str(e)}"
        return data

    def getUserProfile(self, user):
        data = Data()
        url = f"{self.base_urls['profile']}/{user}"
        try:
            response = self.request("GET", url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            response_data = response.json()
            data.name = response_data["user"]["name"]
            data.avtr = response_data["user"]["avatar"]
        except requests.exceptions.RequestException as e:
            data.error = True
            data.error_info = str(e)
        except (ValueError, KeyError) as e:
            data.error = True
            data.error_info = f"JSON parsing error or key error: {str(e)}"
        return data

    def getAllUsers(self, group=False, profiles=False):
        page = 0
        while True:
            url = f"{self.base_urls['profile']}?page={page}"
            if group:
                url = f"{self.base_urls['group']}?page={page}"
            try:
                response = self.request("GET", url, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                response_data = response.json()
                total_pages = response_data["totalPages"]
                for user in response_data["users"]:
                    profile = None
                    if profiles:
                        profile = self.getUserProfile(user["id"])
                    yield user, page, total_pages, profile
                page += 1
                if page >= total_pages:
                    break
            except requests.exceptions.RequestException as e:
                logging.error(f"Request error: {str(e)}")
                break
            except (ValueError, KeyError) as e:
                logging.error(f"JSON parsing error or key error: {str(e)}")
                break
            time.sleep(1)

if __name__ == "__main__":
    # Example usage
    user_id = '6aaf625a-2252-4ca9-8edf-19041cee4b61'
    freerice = Freerice(user_id=user_id)

    # Start a new game
    game_data = freerice.newGame()
    if game_data.error:
        print(f"Error starting new game: {game_data.error_info}")
    else:
        print(f"New game started. Question: {game_data.question_txt}")

    # Submit an answer to the current question
    answer_result = freerice.submitAnswer(game_data.question_id, 'your_answer_choice')
    if answer_result.error:
        print(f"Error submitting answer: {answer_result.error_info}")
    else:
        print(f"Answer submitted. New streak: {answer_result.streak}, Total rice: {answer_result.rice_total}")

    # Get user statistics
    user_stats = freerice.getUserStats(user=user_id)
    if user_stats.error:
        print("Error retrieving user stats.")
    else:
        print(f"User stats: Rice total = {user_stats.rice_total_all}, Rank = {user_stats.rank}")

    # Get user profile
    user_profile = freerice.getUserProfile(user=user_id)
    if user_profile.error:
        print("Error retrieving user profile.")
    else:
        print(f"User profile: Name = {user_profile.name}, Avatar = {user_profile.avtr}")

    # Retrieve all users (example of iterating through all users)
    for user, page, total_pages, profile in freerice.getAllUsers():
        print(f"User: {user}, Page: {page}/{total_pages}, Profile: {profile}")
