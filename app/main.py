from crews.travel_crew import run_travel_plan


def main():
    report = run_travel_plan(
        user_request=(
            "Me and my Friend want to travel from Delhi to Rishikesh "
            "for 5 days with a budget of INR 30,000 on 12-07-2026."
        )
    )
    print("Final Result:\n", report)


if __name__ == "__main__":
    main()
