import paramak
import argparse

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Generate a pressure vessel STEP file with specified rotation angle and thickness."
    )
    parser.add_argument(
        "--rotation_angle",
        type=int,
        required=True,
        choices=range(1, 361),
        default=180,
        help="Rotation angle for the pressure vessel (must be between 1 and 360 degrees). Default is 180deg."
    )
    parser.add_argument(
        "--thickness",
        type=float,
        default=2.5,
        help="Thickness of the pressure vessel (default is 2.5 cm)."
    )

    # Parse arguments
    args = parser.parse_args()
    rotation_angle = args.rotation_angle
    thickness = args.thickness

    print(f"Set rotation_angle as {rotation_angle} degrees")
    print(f"Set thickness as {thickness} cm")

    # Define the pressure vessel
    pressure_vessel = paramak.BlanketFP(
        minor_radius=220,
        major_radius=580,
        elongation=1,
        triangularity=0.3,
        thickness=thickness,
        start_angle=-270,
        stop_angle=90,
        rotation_angle=rotation_angle,  # Use the argument here
        num_points=200
    )

    # Export the STEP file
    output_filename = f'./w7xPV.stp'
    pressure_vessel.export_stp(output_filename, units='cm')
    print(f"Pressure vessel exported as {output_filename}")

if __name__ == "__main__":
    main()
