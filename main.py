import argparse

from package import actimagine

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    args = parser.parse_args()
    
    act = actimagine.ActImagine()
    with open(args.filename, "rb") as f:
        data = f.read()
    act.load_vx(data)
    act.interpret_vx()

if __name__ == "__main__":
    main()

