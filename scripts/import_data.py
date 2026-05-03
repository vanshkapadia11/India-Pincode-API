import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app import models

# create tables if not exists
models.Base.metadata.create_all(bind=engine)


def import_data(csv_path: str):
    print("Reading CSV...")
    df = pd.read_csv(csv_path, dtype=str)

    # rename columns to match our model
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    print(f"Columns found: {list(df.columns)}")
    print(f"Total rows: {len(df)}")

    # rename to match our DB columns
    df = df.rename(
        columns={
            "officename": "post_office",
            "officetype": "office_type",
            "deliverystatus": "delivery",
            "divisionname": "division",
            "regionname": "region",
            "circlename": "circle",
            "taluk": "taluk",
            "districtname": "district",
            "statename": "state",
            "pincode": "pincode",
        }
    )

    # keep only columns we need
    keep = [
        "pincode",
        "post_office",
        "office_type",
        "delivery",
        "division",
        "region",
        "circle",
        "taluk",
        "district",
        "state",
    ]
    df = df[[c for c in keep if c in df.columns]]

    # drop rows where pincode is missing
    df = df.dropna(subset=["pincode"])
    df = df[df["pincode"].str.match(r"^\d{6}$")]

    print("Importing into database... this may take a minute.")

    db = SessionLocal()
    try:
        batch = []
        for i, row in df.iterrows():
            batch.append(models.Pincode(**row.to_dict()))

            # insert in batches of 1000
            if len(batch) == 1000:
                db.bulk_save_objects(batch)
                db.commit()
                batch = []
                print(f"Inserted {i+1} rows...", end="\r")

        # insert remaining
        if batch:
            db.bulk_save_objects(batch)
            db.commit()

        print(f"\n✅ Done! Total imported: {len(df)} records")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_data.py path/to/pincode.csv")
        sys.exit(1)

    import_data(sys.argv[1])
