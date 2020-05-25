"""main entry for fortlab command-line interface"""


def main():
    from fortlab import Fortlab
    ret, _ = Fortlab().run_command()
    return ret


if __name__ == "__main__":
    main()
