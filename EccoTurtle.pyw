from ecco import run

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        from ecco.game import _msgbox
        _msgbox("Error", f"{e}\n\nTry:\n- pip install --upgrade pygame\n- Python 3.10-3.12")
