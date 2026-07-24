from pathlib import Path

def main():
    print("=" * 40)
    print("🚀 Project Audo")
    print("=" * 40)

    project_root = Path(__file__).resolve().parent.parent

    print(f"Project Root : {project_root}")
    print("System Started Successfully")


if __name__ == "__main__":
    main()