import asyncio
import httpx

URL = "http://127.0.0.1:8000/reservations"

payload = {
    "seat_number": "C1",
    "customer_name": "StressUser",
    "customer_email": "stress@test.com",
    "movie_id": "MOVIE1"
}

async def send_request(i, client):
    try:
        r = await client.post(URL, json=payload, timeout=10)
        try:
            data = r.json()
        except:
            data = r.text

        return {
            "client": i,
            "status": r.status_code,
            "response": data
        }

    except Exception as e:
        return {
            "client": i,
            "status": "ERROR",
            "response": str(e)
        }


async def main():
    async with httpx.AsyncClient() as client:

        # 🔥 STEP 1: heavy concurrency load
        tasks = [send_request(i, client) for i in range(20)]
        results = await asyncio.gather(*tasks)

        # 🔥 STEP 2: analysis
        success = []
        conflicts = []

        for r in results:
            print(r)

            if r["status"] == 200:
                success.append(r)

            elif r["status"] == 409:
                conflicts.append(r)
        print("\n--- RESULTS ---")
        print("Success count:", len(success))
        print("Conflict count:", len(conflicts))

        print("\n--- SAMPLE SUCCESS ---")
        if success:
            print(success[0])

        print("\n--- SAMPLE CONFLICT ---")
        if conflicts:
            print(conflicts[0])

        # 🔥 STEP 3: FINAL VERIFICATION (important!)
        check = await client.get("http://127.0.0.1:8000/seats")
        print("\n--- FINAL SEAT STATE ---")
        print(check.json())


asyncio.run(main())