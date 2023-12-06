import logging
from restclient import cli



def main():
    print('Running main')
    logging.basicConfig(
        filename='run.log',
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO,
    )
    cli.execute()


if __name__ == '__main__':
    main()

