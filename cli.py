import argparse

from mess import Mess


def main():
    parser = argparse.ArgumentParser(description="Convert mess files to and from json and dir")
    parser.add_argument("path", help="Path of the mess file")

    convert = parser.add_mutually_exclusive_group(required=True)
    convert.add_argument("--to-json", metavar="FILE", help="Read the mess file and write to a json file")
    convert.add_argument("--to-dir", metavar="DIR", help="Read the mess file and write a dir")
    convert.add_argument("--from-json", metavar="FILE", help="Write the mess file from a json file")
    convert.add_argument("--from-dir", metavar="DIR", help="Write the mess file from a dir")

    args = parser.parse_args()

    mess = Mess()

    if args.to_json:
        mess.read(args.path)
        with open(args.to_json, "w", encoding="utf-8") as json_file:
            json_file.write(mess.to_json())
    elif args.to_dir:
        mess.read(args.path)
        mess.to_dir(args.to_dir)
    elif args.from_json:
        mess.from_json(open(args.from_json, encoding="utf-8").read())
        mess.write(args.path)
    else:
        mess.from_dir(args.from_dir)
        mess.write(args.path)


if __name__ == "__main__":
    main()