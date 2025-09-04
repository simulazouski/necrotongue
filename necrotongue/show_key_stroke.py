from pynput import keyboard


def on_press(key):
    print("----------")
    print(f"Raw: {repr(key)}")

    if isinstance(key, keyboard.KeyCode):
        print("🟡 KeyCode:")
        print(f"  - char: {key.char}")
        print(f"  - vk: {key.vk}")

    elif isinstance(key, keyboard.Key):
        print("🔵 Special Key:")
        print(f"  - name: {key.name}")
        print(f"  - value: {key.value}")

    else:
        print("🔴 Unknown key type:", type(key))


def on_release(key):
    if key == keyboard.Key.esc:
        print("Exiting...")
        return False  # Stop listener on Esc


print("▶️ Press any key (Esc to quit)...")
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
