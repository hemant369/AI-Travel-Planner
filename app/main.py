from crews.travel_crew import travel_crew

def main():
    result = travel_crew.kickoff(
       inputs={
            "user_request": (
                """Me and my Friend want to travel from Delhi to Rishikesh
                for 5 days with a budget of ₹30,000 on 12-07-2026."""
            )
       }
    )

    print("Final Result:", result)

if __name__ == "__main__":
    main()