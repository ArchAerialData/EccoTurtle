def _fallback_msgbox(title, text):
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, text, title, 0x40)
    except Exception:
        print(f"{title}: {text}")

if __name__ == "__main__":
    try:
        from ecco import run
        run()
    except Exception as e:
        try:
            # Try to use the game's nicer message box if available
            from ecco.game import _msgbox as _msg
        except Exception:
            _msg = _fallback_msgbox
        _msg("Error", f"{e}\n\nTry:\n- pip install --upgrade pygame\n- Python 3.10-3.12")
