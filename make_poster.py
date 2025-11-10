# file make_poster.py
from poster_designer import build_poster

if __name__ == "__main__":
    build_poster("sample_poster.json", "MyPoster.pdf")
    print("Done. Wrote MyPoster.pdf")
