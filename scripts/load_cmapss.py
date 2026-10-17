"""Script to load C-MAPSS turbofan dataset files into PostgreSQL tables."""

from pathlib import Path

from sqlalchemy.orm import Session

from api.db.reliability_models import EngineCycle, EngineLife
from api.db.session import SessionLocal


def load_cmapss_data(data_dir: str = "data/cmapss") -> None:
    """Load turbofan txt files from data_dir into engine_cycles and engine_life tables."""
    path = Path(data_dir)
    if not path.exists():
        print(f"Data directory {data_dir} does not exist. Skipping load.")
        return

    db: Session = SessionLocal()
    try:
        # Example loader logic for train_FD001.txt format:
        # unit_id, cycle, setting_1, setting_2, setting_3, s_1 ... s_21
        for txt_file in path.glob("*.txt"):
            dataset_name = txt_file.stem
            print(f"Loading {dataset_name} into database...")
            lines = txt_file.read_text(encoding="utf-8").splitlines()
            
            unit_max_cycles: dict[int, int] = {}

            for line in lines:
                parts = line.strip().split()
                if len(parts) < 5:
                    continue
                unit_id = int(parts[0])
                cycle = int(parts[1])
                setting_1 = float(parts[2])
                setting_2 = float(parts[3])
                setting_3 = float(parts[4])

                cycle_obj = EngineCycle(
                    dataset_name=dataset_name,
                    unit_id=unit_id,
                    cycle=cycle,
                    setting_1=setting_1,
                    setting_2=setting_2,
                    setting_3=setting_3,
                )
                db.add(cycle_obj)

                if unit_id not in unit_max_cycles or cycle > unit_max_cycles[unit_id]:
                    unit_max_cycles[unit_id] = cycle

            db.commit()

            # Populate engine_life summary per unit
            for unit_id, max_cycle in unit_max_cycles.items():
                life_obj = EngineLife(
                    dataset_name=dataset_name,
                    unit_id=unit_id,
                    time_to_failure=float(max_cycle),
                    event_observed=1,
                )
                db.add(life_obj)
            db.commit()
            print(f"Finished loading {dataset_name}.")
    except Exception as exc:
        db.rollback()
        print(f"Error loading C-MAPSS data: {exc}")
    finally:
        db.close()


if __name__ == "__main__":
    load_cmapss_data()
