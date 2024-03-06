import click
from urllib.parse import urlparse


def get_last_part_of_url(url):
    parsed_url = urlparse(url)
    path = parsed_url.path
    # Remove leading and trailing slashes
    path = path.strip("/")
    # Split the path by slashes and return the last part
    return path.split("/")[-1]


@click.command()
@click.option("--url", required=True)
def run(url: str) -> None:
    print(get_last_part_of_url(url))


if __name__ == "__main__":
    run()
