from typing import List, Tuple, Any

def get_choices(constants_class: Any) -> List[Tuple[str, str]]:
    return [
        (value, value)
        for key, value in vars(constants_class).items()
        if not key.startswith('__')
    ]