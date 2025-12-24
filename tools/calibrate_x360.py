"""
x360 Calculator for CS2/CSGO

This tool calculates the x360 value based on your in-game sensitivity settings.

CS2/CSGO uses a fixed yaw rate of 0.022 degrees per mouse count at sensitivity 1.0.
This means:
    x360 = 360 / (0.022 * sensitivity) = 16363.6 / sensitivity

For example:
    - Sensitivity 1.0  → x360 = 16364
    - Sensitivity 2.0  → x360 = 8182
    - Sensitivity 0.5  → x360 = 32727

Usage:
    python calibrate_x360.py                    # Interactive mode
    python calibrate_x360.py --sensitivity 1.5  # Direct calculation
    python calibrate_x360.py --test 16364       # Test a value in-game
"""

import sys
import argparse
import time

try:
    import keyboard
except ImportError:
    keyboard = None


# CS2/CSGO constants
# The game uses 0.022 degrees per mouse count at sensitivity 1.0
CSGO_YAW = 0.022
BASE_X360 = 360.0 / CSGO_YAW  # = 16363.636...


def calculate_x360(sensitivity: float, m_yaw: float = CSGO_YAW) -> int:
    """
    Calculate x360 from sensitivity.

    Args:
        sensitivity: In-game sensitivity value
        m_yaw: Yaw rate (default 0.022 for CS2/CSGO)

    Returns:
        x360 value (mouse counts for 360 degree turn)
    """
    if sensitivity <= 0:
        raise ValueError("Sensitivity must be positive")

    x360 = 360.0 / (m_yaw * sensitivity)
    return int(round(x360))


def calculate_sensitivity(x360: int, m_yaw: float = CSGO_YAW) -> float:
    """
    Calculate sensitivity from x360.

    Args:
        x360: Mouse counts for 360 degree turn
        m_yaw: Yaw rate (default 0.022 for CS2/CSGO)

    Returns:
        Sensitivity value
    """
    if x360 <= 0:
        raise ValueError("x360 must be positive")

    sensitivity = 360.0 / (m_yaw * x360)
    return sensitivity


def interactive_mode():
    """Run interactive calculator."""
    print("=" * 60)
    print("x360 CALCULATOR FOR CS2/CSGO")
    print("=" * 60)
    print()
    print("This calculates x360 from your in-game sensitivity.")
    print()
    print("How to find your sensitivity:")
    print("  1. Open CS2 console (~)")
    print("  2. Type: sensitivity")
    print("  3. It will show your current value")
    print()

    while True:
        try:
            sens_input = input("Enter your sensitivity (or 'q' to quit): ").strip()

            if sens_input.lower() == 'q':
                break

            sensitivity = float(sens_input)

            if sensitivity <= 0:
                print("Sensitivity must be a positive number!")
                continue

            x360 = calculate_x360(sensitivity)

            print()
            print("=" * 60)
            print(f"  Sensitivity: {sensitivity}")
            print(f"  >>> x360 = {x360} <<<")
            print("=" * 60)
            print()
            print("Add this to your run.py:")
            print(f"    X360 = {x360}")
            print()

            # Show common sensitivity table
            print("Reference table:")
            print("-" * 30)
            for s in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
                x = calculate_x360(s)
                marker = " <-- YOU" if abs(s - sensitivity) < 0.01 else ""
                print(f"  sens {s:>4.1f}  →  x360 = {x:>5}{marker}")
            print()

        except ValueError:
            print("Please enter a valid number!")
            continue


def test_x360(x360_value: int):
    """Test an x360 value by moving the mouse."""
    if keyboard is None:
        print("ERROR: keyboard module required for testing.")
        print("Install with: pip install keyboard")
        return

    try:
        import win32api
        import win32con
    except ImportError:
        print("ERROR: pywin32 required for testing.")
        print("Install with: pip install pywin32")
        return

    print("=" * 60)
    print(f"TESTING x360 = {x360_value}")
    print("=" * 60)
    print()
    print("This will move your mouse by exactly x360 units.")
    print("In-game, you should rotate exactly 360 degrees.")
    print()
    print("Instructions:")
    print("  1. Alt-Tab into CS2")
    print("  2. Look at a reference point (wall corner, etc)")
    print("  3. Press CAPS LOCK")
    print("  4. You should end up looking at the same point")
    print()
    print("Press CAPS LOCK to start (or Ctrl+C to cancel)...")

    try:
        keyboard.wait(58)
    except KeyboardInterrupt:
        print("\nCancelled.")
        return

    time.sleep(0.2)  # Brief delay

    print("Moving mouse...")

    # Move in small increments for smoothness
    chunk_size = 100
    num_chunks = x360_value // chunk_size
    remainder = x360_value % chunk_size

    for _ in range(num_chunks):
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, chunk_size, 0, 0, 0)
        time.sleep(0.002)

    if remainder:
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, remainder, 0, 0, 0)

    print("Done!")
    print()
    print("Results:")
    print("  - Rotated LESS than 360°?  → Your x360 is too LOW")
    print("  - Rotated MORE than 360°?  → Your x360 is too HIGH")
    print("  - Rotated exactly 360°?    → Perfect!")
    print()

    # Show what sensitivity this corresponds to
    sens = calculate_sensitivity(x360_value)
    print(f"This x360 corresponds to sensitivity {sens:.3f}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="x360 Calculator for CS2/CSGO",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python calibrate_x360.py                     # Interactive mode
  python calibrate_x360.py -s 1.5              # Calculate for sensitivity 1.5
  python calibrate_x360.py --test 16364        # Test x360 value in-game

Common values:
  Sensitivity 1.0  →  x360 = 16364
  Sensitivity 2.0  →  x360 = 8182
  Sensitivity 3.0  →  x360 = 5455
        """
    )

    parser.add_argument(
        "-s", "--sensitivity",
        type=float,
        metavar="VALUE",
        help="Calculate x360 for this sensitivity",
    )

    parser.add_argument(
        "--test",
        type=int,
        metavar="X360",
        help="Test an x360 value by moving the mouse in-game",
    )

    parser.add_argument(
        "--m_yaw",
        type=float,
        default=CSGO_YAW,
        help=f"Custom m_yaw value (default: {CSGO_YAW})",
    )

    args = parser.parse_args()

    if args.test:
        test_x360(args.test)
    elif args.sensitivity:
        x360 = calculate_x360(args.sensitivity, args.m_yaw)
        print(f"Sensitivity {args.sensitivity} → x360 = {x360}")
        print()
        print("Add to run.py:")
        print(f"    X360 = {x360}")
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
