from backend_src.db import AsyncDBSession, Queries
from .schema import ModelDroneRead, UnverifiedModelRead


async def list_unverified(db: AsyncDBSession) -> list[UnverifiedModelRead]:
    models = await Queries.Model.get_unverified(db)
    drones = await Queries.Model.get_drones_of([model.id for model in models], db)

    return [
        UnverifiedModelRead.model_validate({
            **{field: getattr(model, field) for field in UnverifiedModelRead.model_fields if field != "drones"},
            "drones": [ModelDroneRead.from_drone(drone) for drone in drones if drone.model_id == model.id],
        })
        for model in models
    ]
