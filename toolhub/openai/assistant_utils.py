from openai import OpenAI
from openai.types.beta.assistant import Assistant


def retrieve_by_name(client: OpenAI, name: str) -> Assistant | None:
    after = None
    while True:
        retrieved = False
        for assistant in client.beta.assistants.list(order="desc", after=after):
            if assistant.name == name:
                return assistant
            after = assistant.id
            retrieved = True
        if not retrieved:
            break
    return None
