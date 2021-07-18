import sys

from flask import Flask, render_template, request
from clients import TwitchRequests, CopypastaFinder, DadJoke

app = Flask(__name__)
twitch_requests_handler = TwitchRequests.from_id_and_secret_path(
    './twitch_client_id.txt',
    './twitch_client_secret.txt',
)
copypasta_generator = CopypastaFinder()
joke_generator = DadJoke()


@app.route("/search")
def search():
    return render_template("search.html")


@app.route("/search_results", methods=["POST", "GET"])
def search_results():
    if request.method == "GET":
        return (
            'The URL /search_results is accessed directly. Try going to "/search" to look for a category'
        )
    if request.method == "POST":
        results = twitch_requests_handler.search_for_section(
            request.form["category_name"],
        )
        for r in results:
            r['box_art_url'] = r['box_art_url'].replace('52x72', '130x180')
        print(results, file=sys.stderr)
        return render_template("search_results.html", results=results)


@app.route("/form")
def form():
    return render_template("form.html")


@app.route("/streams", methods=["POST", "GET"])
def streams():
    if request.method == "GET":
        return (
            "The URL /streams is accessed directly. Try going to '/form' to get streams info"
        )
    if request.method == "POST":
        twitch_requests_handler.get_streams_info(
            request.form["category_name"],
            int(request.form["max_viewers"]),
        )
        results = twitch_requests_handler.get_sample()
        for r in results:
            r["link"] = "https://twitch.tv/" + r["user_login"]
        pasta = copypasta_generator.random_copypasta()
        joke = joke_generator.get_random_joke()
        return render_template(
            "streams.html",
            results=results,
            pasta=pasta[0],
            pasta_cr=pasta[1],
            joke=joke[0],
            joke_cr=joke[1],
        )


if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
