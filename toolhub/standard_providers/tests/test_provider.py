import datetime
import pydantic

from toolhub.lib import auth
from toolhub.lib import function
from toolhub.lib import provider


def _joke_of_the_day(joke_date: datetime.date) -> str:
    if joke_date >= datetime.date.today():
        return "McDonald’s is the Lebron James of frying potatoes."
    else:
        return "Forgot the joke!"


_joke_of_the_day_spec: function.FunctionSpec = function.FunctionSpec(
    name="joke_of_the_day",
    parameters=[
        function.ParameterSpec(
            name="joke_date",
            type_=datetime.date,
            description="The date",
            required=True,
        ),
    ],
    return_=function.ReturnSpec(
        type_=str,
        description="The joke of the day",
    ),
    description=None,
)
_joke_of_the_day_fn: function.Function = function.Function(
    spec=_joke_of_the_day_spec,
    callable_=auth.no_auth(_joke_of_the_day),
)


def _quote_of_the_day(quote_date: datetime.date) -> str:
    if quote_date >= datetime.date.today():
        return "The power to question is the basis of all human progress."
    else:
        return "Forgot the quote!"


_quote_of_the_day_spec: function.FunctionSpec = function.FunctionSpec(
    name="quote_of_the_day",
    parameters=[
        function.ParameterSpec(
            name="quote_date",
            type_=datetime.date,
            description="The date",
            required=True,
        ),
    ],
    return_=function.ReturnSpec(
        type_=str,
        description="The quote of the day",
    ),
    description=None,
)
_quote_of_the_day_fn: function.Function = function.Function(
    spec=_quote_of_the_day_spec,
    callable_=auth.no_auth(_quote_of_the_day),
)


class Restaurant(pydantic.BaseModel):
    name: str
    location: str


def _foodhub_review(restaurant: Restaurant) -> str | None:
    if (
        restaurant.name == "Palateria Los Manguitos"
        and restaurant.location == "Redwood City"
    ):
        return "Delightful!"
    else:
        return None
    return None


_foodhub_review_spec: function.FunctionSpec = function.FunctionSpec(
    name="foodhub_review",
    parameters=[
        function.ParameterSpec(
            name="restaurant",
            type_=Restaurant,
            description="The restaurant.",
            required=True,
        ),
    ],
    return_=function.ReturnSpec(
        type_=str,
        description="The review for the restaurant, if present",
    ),
    description=None,
)
_foodhub_review_fn: function.Function = function.Function(
    spec=_foodhub_review_spec,
    callable_=auth.no_auth(_foodhub_review),
)


class Provider(provider.Provider):
    _functions: dict[str, function.Function] = {
        fn.spec.name: fn
        for fn in (
            _joke_of_the_day_fn,
            _quote_of_the_day_fn,
            _foodhub_review_fn,
        )
    }
    _collections: dict[str, function.FunctionCollection] = {
        col.name: col
        for col in (
            function.FunctionCollection(
                name="jokes",
                description="functions that tell jokes",
                function_names={_joke_of_the_day_spec.name},
            ),
            function.FunctionCollection(
                name="quotes",
                description="functions that share quotes",
                function_names={_quote_of_the_day_spec.name},
            ),
        )
    }

    def functions(self) -> list[function.Function]:
        return self._functions

    def collections(self) -> list[function.FunctionCollection]:
        return self._collections
