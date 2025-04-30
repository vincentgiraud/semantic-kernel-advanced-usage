import tracing
import logging
from dapr.ext.fastapi import DaprActor
from fastapi import FastAPI
from contextlib import asynccontextmanager
from sk_actor import SKAgentActor

logger = logging.getLogger(__name__)


tracing.set_up_logging()
tracing.set_up_tracing()
tracing.set_up_metrics()


actor: DaprActor = None

# Register actor when fastapi starts up


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Registering actor")
    await actor.register_actor(SKAgentActor)
    yield


# Create fastapi and register dapr and actors
app = FastAPI(title="SK Agent Dapr Actors host", lifespan=lifespan)
actor = DaprActor(app)
