"""
Seed 1000 Realistic Daily Work & Cost Logs
Generates realistic multi-site visit records for 5-6 technicians across dates.
Covers advances, materials, petrol, nashta/conveyance, direct seth payments, and inspections.
"""
import random
from datetime import datetime, timedelta
from database.db_connection import DatabaseConnection


FIRST_NAMES = [
    "Ramesh", "Suresh", "Amit", "Rahul", "Pooja", "Vikram", "Sunil", "Anil", "Deepak", "Priya",
    "Manish", "Rajeev", "Neeraj", "Sanjay", "Alok", "Vikas", "Pankaj", "Rohit", "Gaurav", "Kavita",
    "Ashish", "Vivek", "Dinesh", "Manoj", "Pradeep", "Sachin", "Nitin", "Tarun", "Sumit", "Anurag",
    "Mukesh", "Harish", "Kapil", "Varun", "Mohit", "Arun", "Jitendra", "Ajay", "Vijay", "Kamal"
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Singh", "Kumar", "Yadav", "Mishra", "Patel", "Chauhan", "Joshi",
    "Pandey", "Saxena", "Bhatnagar", "Agarwal", "Bansal", "Goel", "Tyagi", "Shukla", "Tiwari", "Rawat",
    "Dubey", "Tripathi", "Srivastava", "Chaudhary", "Malhotra", "Kapoor", "Arora", "Bhardwaj", "Seth", "Rao"
]

BUSINESSES = [
    "Apex Diagnostic Centre", "Shree Ram Sweets", "Apollo Pharmacy", "Logix Dental Clinic",
    "Modern Garments Store", "Gupta Electronics", "Krishna Supermarket", "Bakers Treat Cafe",
    "Dr. Batra Eye Clinic", "City Fitness Gym", "Hotel Grand Residency", "Sharma Law Chambers",
    "Green Valley Public School", "Shri Ganesh Medical Hall", "Reliance Smart Point Site",
    "Aggarwal Sweet Corner", "Trends Boutique", "Chai Point Outpost", "Max Health Poly Clinic"
]

LOCALITIES = [
    "Sector 15, Noida", "Sector 18, Noida", "Sector 62, Noida", "Sector 74, Supertech Capetown, Noida",
    "Sector 78, Mahagun Moderne, Noida", "Sector 137, Paras Tierea, Noida", "Sector 121, Homes 121, Noida",
    "Sector 50, Noida", "Sector 76, Amrapali Silicon, Noida", "Sector 128, Jaypee Greens, Noida",
    "Gaur City 1, Greater Noida West", "Gaur City 2, 14th Avenue, Greater Noida West",
    "Alpha 1, Commercial Belt, Greater Noida", "Beta 2, Greater Noida", "Omicron 3, Greater Noida",
    "Indirapuram, Habitat Centre, Ghaziabad", "Indirapuram, Ahinsa Khand 2, Ghaziabad",
    "Vaishali Sector 4, Ghaziabad", "Vasundhara Sector 11, Ghaziabad", "Raj Nagar Extension, Ghaziabad",
    "Mayur Vihar Phase 1, Pocket 4, Delhi", "Mayur Vihar Phase 2, Pocket C, Delhi",
    "Laxmi Nagar, Main Market, Delhi", "Preet Vihar, Block D, Delhi", "Karkardooma, Delhi",
    "South Extension Part 1, Delhi", "Lajpat Nagar 4, Delhi", "Dwarka Sector 12, Delhi",
    "DLF Phase 3, Gurgaon", "Sohna Road, Sector 48, Gurgaon", "Golf Course Road, Gurgaon"
]

WORK_TEMPLATES = [
    # (work_desc, min_mat, max_mat, min_pet, max_pet, min_bill, max_bill, has_advance_prob, mat_details)
    (
        "1.5-Ton Split AC Gas Charging (R32) & Copper pipe brazing leak repair",
        700, 1100, 100, 180, 2200, 3200, 0.65,
        ["1kg R32 Refrigerant Gas", "Brazing rod & Flux", "1/4 Flare nut replacement"]
    ),
    (
        "Inverter Split AC PCB Repair & 45uF Compressor Capacitor replacement",
        400, 850, 80, 160, 1600, 2600, 0.40,
        ["Running Capacitor 45uF", "PCB relay & diode replacement", "Thermal paste"]
    ),
    (
        "2x Split AC Jet Pump Master Cleaning, Coil Chemical Wash & Drain Pipe flush",
        0, 0, 100, 160, 1000, 1800, 0.15,
        ["Chemical Coil Cleaner spray"]
    ),
    (
        "Site Visit: AC Not Cooling inspection, Gas pressure testing & estimate provided",
        0, 0, 120, 220, 350, 500, 0.05,
        ["Inspection & diagnostic check"]
    ),
    (
        "1.5-Ton Split AC Complete Shifting, New Outdoor Stand & 10ft Copper Piping",
        1800, 3200, 150, 280, 4200, 6200, 0.80,
        ["10ft Copper Pipe set with insulation", "Heavy duty outdoor stand", "Fasteners & drain pipe"]
    ),
    (
        "Window AC 1.5-Ton Fan Motor Replacement & Capacitor change",
        1100, 1700, 90, 160, 2400, 3400, 0.50,
        ["Double shaft fan motor", "Dual capacitor 50+5 uF"]
    ),
    (
        "Cassette AC 2-Ton Service, Indoor Blower cleaning & Contactor replacement",
        500, 950, 120, 200, 2500, 3800, 0.40,
        ["3-Pole Heavy duty contactor", "Filter cleaning"]
    ),
    (
        "AC Water Leakage repairing, Tray cleaning & 5m Flexible Drain Pipe install",
        150, 300, 80, 140, 800, 1400, 0.20,
        ["5m Flexible drain pipe", "Insulation tape", "M-Seal & clamp"]
    ),
    (
        "Site Visit & Troubleshooting: MCB tripping due to outdoor earthing fault fixed",
        50, 150, 100, 180, 600, 1000, 0.10,
        ["20A MCB replacement & 2.5mm copper wire piece"]
    ),
    (
        "General AC Checkup & Remote Sensor receiver replacement",
        250, 450, 70, 130, 900, 1500, 0.25,
        ["Universal remote sensor display PCB & Remote"]
    )
]

EXTRA_NOTES = [
    "Work completed smoothly, customer satisfied.",
    "Advance collected for purchasing spare parts from market.",
    "Customer paid full amount on site in cash.",
    "Direct payment sent by customer via GooglePay to Seth.",
    "Site visit only, customer will call back next week for parts approval.",
    "Tea & Snacks expense ₹50 added to travel cost.",
    "Customer requested evening 6 PM call back for maintenance contract.",
    "Fast service completed within 45 minutes.",
    "Parts purchased from local refrigeration wholesale market.",
    "Customer promised to clear remaining balance by tomorrow morning."
]


def seed_daily_logs(target_count=1000):
    db = DatabaseConnection()

    # Get active technicians
    tech_rows = db.execute_query(
        "SELECT id, name, mobile FROM technicians WHERE is_active = 1 LIMIT 6",
        fetch_all=True
    ) or []

    if not tech_rows:
        print("[ERROR] No active technicians found in database!")
        return

    print(f"[INFO] Seeding with {len(tech_rows)} technicians:")
    for t in tech_rows:
        print(f"  - ID: {t['id']} | {t['name']}")

    # Date range: past 210 days up to today
    today = datetime.now().date()
    start_date = today - timedelta(days=210)

    # Prepare batch insert
    insert_sql = """
    INSERT INTO daily_logs (
        log_date, customer_name, customer_mobile, customer_address,
        customer_id, technician_id, technician_name, work_description,
        total_billed, advance_payment, advance_receiver,
        final_payment, final_receiver, total_payment, pending_amount,
        material_cost, petrol_expense, total_expense,
        payment_status, payment_mode, net_profit, notes, is_active,
        created_at, updated_at
    ) VALUES (
        %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s,
        %s, %s, %s, %s, 1,
        %s, %s
    )
    """

    params_list = []

    for i in range(target_count):
        # Choose technician round-robin with small randomness
        tech = tech_rows[i % len(tech_rows)]

        # Generate date (randomly distributed between start_date and today)
        random_days = random.randint(0, 210)
        log_date = start_date + timedelta(days=random_days)
        log_date_str = log_date.strftime("%Y-%m-%d")

        # Customer generation (80% Individual, 20% Commercial/Business)
        if random.random() < 0.20:
            cust_name = random.choice(BUSINESSES)
        else:
            cust_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

        mobile = f"98{random.randint(10000000, 99999999)}"

        # Address
        house_num = f"{random.choice(['Flat', 'House', 'Plot', 'Shop', 'Villa', 'Office'])} {random.randint(1, 999)}"
        cust_address = f"{house_num}, {random.choice(LOCALITIES)}"

        # Work & Finance template
        template = random.choice(WORK_TEMPLATES)
        work_desc_base, min_mat, max_mat, min_pet, max_pet, min_bill, max_bill, adv_prob, parts_list = template

        material_cost = float(random.randint(min_mat // 50, max_mat // 50) * 50) if max_mat > 0 else 0.0
        petrol_expense = float(random.randint(min_pet // 10, max_pet // 10) * 10)

        # 25% chance to add small tea/nashta/conveyance to petrol expense
        if random.random() < 0.30:
            petrol_expense += float(random.choice([30, 40, 50, 60]))

        total_expense = material_cost + petrol_expense

        total_billed = float(random.randint(min_bill // 100, max_bill // 100) * 100)

        # Advance & Final Payment distribution
        r_type = random.random()
        if r_type < adv_prob and total_billed >= 1000:
            # Has Advance
            adv_ratio = random.choice([0.25, 0.30, 0.40, 0.50])
            advance_payment = float(round((total_billed * adv_ratio) / 100) * 100)
            
            # Who received advance? (80% Tech, 20% Direct Seth)
            if random.random() < 0.80:
                advance_receiver = random.choice(["Tech (Cash)", "Tech (UPI)"])
            else:
                advance_receiver = "Direct Seth (UPI/Bank)"

            # Final payment (85% paid, 15% pending balance)
            if random.random() < 0.85:
                final_payment = total_billed - advance_payment
                if random.random() < 0.75:
                    final_receiver = random.choice(["Tech (Cash)", "Tech (UPI)"])
                else:
                    final_receiver = "Direct Seth (UPI/Bank)"
                payment_status = "Paid"
            else:
                final_payment = 0.0
                final_receiver = "Pending"
                payment_status = "Partial (Advance Paid)"

        else:
            # No advance (Single full payment or pending)
            advance_payment = 0.0
            advance_receiver = "Tech (Cash)"

            if random.random() < 0.90:
                # Full payment on completion
                final_payment = total_billed
                if random.random() < 0.75:
                    final_receiver = random.choice(["Tech (Cash)", "Tech (UPI)"])
                else:
                    final_receiver = "Direct Seth (UPI/Bank)"
                payment_status = "Paid"
            else:
                # Fully pending
                final_payment = 0.0
                final_receiver = "Pending"
                payment_status = "Pending"

        total_payment = advance_payment + final_payment
        pending_amount = max(0.0, total_billed - total_payment)
        net_profit = total_payment - total_expense

        payment_mode = random.choice(["Cash", "Cash", "Cash", "UPI / GPay / PhonePe", "Bank Transfer (NEFT/IMPS)"])

        # Parts description embellishment
        if material_cost > 0:
            parts_str = ", ".join(parts_list)
            full_work_desc = f"{work_desc_base} [Parts: {parts_str} (₹{int(material_cost)})]"
        else:
            full_work_desc = work_desc_base

        notes = random.choice(EXTRA_NOTES)
        created_at = f"{log_date_str} {random.randint(9, 19):02d}:{random.randint(10, 59):02d}:00"

        params_list.append((
            log_date_str, cust_name, mobile, cust_address,
            None, tech['id'], tech['name'], full_work_desc,
            total_billed, advance_payment, advance_receiver,
            final_payment, final_receiver, total_payment, pending_amount,
            material_cost, petrol_expense, total_expense,
            payment_status, payment_mode, net_profit, notes,
            created_at, created_at
        ))

    print(f"[INFO] Inserting {len(params_list)} daily log records into database...")

    # Execute in transaction
    try:
        # Batch insert in chunks of 100
        chunk_size = 100
        total_inserted = 0
        for idx in range(0, len(params_list), chunk_size):
            chunk = params_list[idx:idx + chunk_size]
            for p in chunk:
                db.execute_query(insert_sql, p)
            total_inserted += len(chunk)
            print(f"  -> Inserted {total_inserted}/{len(params_list)} records...")

        print(f"[SUCCESS] Successfully seeded {len(params_list)} realistic daily work & cost logs!")
    except Exception as e:
        print(f"[ERROR] Failed to seed daily logs: {e}")


if __name__ == "__main__":
    seed_daily_logs(1000)
