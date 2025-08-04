#!/usr/bin/env python
# -=-<[ Bismillahirrahmanirrahim ]>-=-
# -*- coding: utf-8 -*-
# @Date    : 2021-05-08 16:51:20
# @Author  : Dahir Muhammad Dahir
# @Description : something cool


from sqlalchemy import Result, Select, String, cast, event, false, or_, select
from app.mixins.commons import DateRange
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.elements import and_
from sqlalchemy.sql.functions import func
from app.mixins.schemas import BaseModelSearch, JoinSearch
from app.utils.enums import ActionStatus
from app.config import database as db
from typing import Any, AsyncGenerator
from pydantic.main import BaseModel

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException

# from app.config.config import settings


async def get_db() -> AsyncGenerator[Any, Any]:
    async with db.db_session_manager.session() as session:
        yield session


class CrudUtil:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db: AsyncSession = db

    async def create_model(
        self, model_to_create: Any, create: BaseModel, autocommit: bool = True
    ) -> Any:
        try:
            columns: set[str] = set(model_to_create.__table__.c.keys())
            create_columns: set[str] = set(create.model_dump().keys())

            db_model = model_to_create(
                **create.model_dump(exclude=set(create_columns - columns))
            )

            if not autocommit:
                await self.__add_no_commit(db_model)
                return db_model
            else:
                await self.__add_and_commit(db_model)
                return db_model

        except IntegrityError as e:
            print(f"Captured exception log: {e}")
            raise HTTPException(
                status_code=403,
                detail=f"Cannot create {model_to_create.__qualname__}, \
                    possible duplicate or invalid attributes",
            )

    async def create_model_multiple(
        self, model_to_create: Any, create: list[Any], autocommit: bool = True
    ) -> Any:
        try:
            columns: set[str] = set(model_to_create.__table__.c.keys())
            create_columns: set[str] = set(create[0].model_dump().keys())

            db_models = [
                model_to_create(
                    **create_item.model_dump(exclude=set(create_columns - columns))
                )
                for create_item in create
            ]

            if not autocommit:
                await self.__add_no_commit(db_models)
                return db_models
            else:
                await self.__add_and_commit(db_models)
                return db_models

        except IntegrityError as e:
            print(f"Captured exception log: {e}")
            raise HTTPException(
                status_code=403,
                detail=f"Cannot create {model_to_create.__qualname__}, \
                    possible duplicate or invalid attributes",
            )

    async def get_model_or_404(
        self,
        model_to_get: Any,
        model_conditions: dict[str, Any] = {},
        order_by_column: str = "id",
        order: str = "asc",
        custom_error: str = "",
    ) -> Any:
        try:
            conditions: list[Any] = []
            for field_name in model_conditions:
                if model_conditions[field_name] is not None:
                    conditions.append(
                        and_(
                            getattr(model_to_get, field_name)
                            == model_conditions[field_name]
                        )
                    )

            query: Select = select(model_to_get).filter(and_(*conditions))

            if order != "asc":
                query = query.order_by(getattr(model_to_get, order_by_column).desc())

                return self.__result_or_404(await self.db.execute(query))

            return self.__result_or_404(await self.db.execute(query))

        except AttributeError:
            raise HTTPException(
                status_code=403,
                detail=f"Invalid attribute for {model_to_get.__qualname__}",
            )

        except Exception as e:
            print(f"Captured exception log: {e}")
            if custom_error:
                raise HTTPException(404, detail=custom_error)

            raise HTTPException(404, detail=f"{model_to_get.__qualname__} not found")

    async def get_model_multiple(
        self,
        model_to_get: Any,
        model_field: str,
        model_field_values: list[Any],
        order_by_column: str = "id",
        order: str = "asc",
    ) -> Any:
        try:
            conditions: list[Any] = []
            for field_value in model_field_values:
                conditions.append(getattr(model_to_get, model_field) == field_value)

            query: Select = select(model_to_get).filter(or_(*conditions))

            if order != "asc":
                query = query.order_by(getattr(model_to_get, order_by_column).desc())
                result: Result[Any] = await self.db.execute(query)
                return result.unique().scalars().all()

            result: Result[Any] = await self.db.execute(query)
            return result.unique().scalars().all()

        except AttributeError:
            raise HTTPException(
                status_code=403,
                detail=f"Invalid attribute for {model_to_get.__qualname__}",
            )

        except Exception as e:
            print(f"Captured exception log: {e}")
            raise HTTPException(404, detail=f"{model_to_get.__qualname__} not found")

    async def get_model_or_none(
        self,
        model_to_get: Any,
        model_conditions: dict[str, Any] = {},
        order_by_column: str = "id",
        order: str = "asc",
        conjunction: str = "and",
    ) -> Any:
        try:
            conditions: list[Any] = []
            for field_name in model_conditions:
                if model_conditions[field_name] is not None:
                    if conjunction == "or":
                        conditions.append(
                            getattr(model_to_get, field_name)
                            == model_conditions[field_name]
                        )
                    else:
                        conditions.append(
                            and_(
                                getattr(model_to_get, field_name)
                                == model_conditions[field_name]
                            )
                        )

            if conjunction == "or":
                query = select(model_to_get).filter(or_(false(), *conditions))
                if order != "asc":
                    query.order_by(getattr(model_to_get, order_by_column).desc())

                return self.__result_or_none(await self.db.execute(query))

            query: Select = select(model_to_get).filter(and_(*conditions))

            if order != "asc":
                query = query.order_by(getattr(model_to_get, order_by_column).desc())

            return self.__result_or_none(await self.db.execute(query))

        except AttributeError:
            raise HTTPException(
                status_code=403,
                detail=f"Invalid attribute for {model_to_get.__qualname__}",
            )

        except Exception as e:
            print(f"Captured exception log: {e}")
            return None

    async def get_model_by_fuzzy_match_or_404(
        self,
        model_to_get: Any,
        model_conditions: dict[str, Any] = {},
        order_by_column: str = "id",
        order: str = "asc",
    ) -> Any:
        try:
            conditions: list[Any] = []
            for field_name in model_conditions:
                if model_conditions[field_name] is not None:
                    conditions.append(
                        getattr(model_to_get, field_name).ilike(
                            f"%{model_conditions[field_name]}%"
                        )
                    )

            query: Select = select(model_to_get).filter(or_(*conditions))

            if order != "asc":
                query = query.order_by(getattr(model_to_get, order_by_column).desc())
                return self.__result_or_404(await self.db.execute(query))

            return self.__result_or_404(await self.db.execute(query))

        except AttributeError:
            raise HTTPException(
                status_code=403,
                detail=f"Invalid attribute for {model_to_get.__qualname__}",
            )

        except Exception as e:
            print(f"Captured exception log: {e}")
            raise HTTPException(404, detail=f"{model_to_get.__qualname__} not found")

    async def update_model(
        self,
        model_to_update: Any,
        update: BaseModel,
        update_conditions: dict[str, Any] = {},
        autocommit: bool = True,
    ) -> Any:
        db_model = await self.get_model_or_404(
            model_to_get=model_to_update, model_conditions=update_conditions
        )

        try:
            if not autocommit:
                await self.__update_no_commit(db_model, update)
                return db_model
            else:
                await self.__update_and_commit(db_model, update)
                return db_model

        except Exception as e:
            print(f"Captured exception log: {e}")
            raise HTTPException(
                status_code=403, detail=f"{model_to_update.__qualname__} update failed"
            )

    async def list_model(
        self,
        model_to_list: Any,
        list_conditions: dict[str, Any] = {},
        date_range: DateRange | None = None,
        skip: int = 0,
        limit: int | None = 100,
        order_by_column: str = "id",
        order: str = "asc",
        count_by_column: str = "id",
        join_conditions: dict[Any, Any] = {},
        sum_by_column: str | None = None,
        conjunction: str = "and",
    ) -> dict[str, Any]:
        if "limit" in list_conditions:
            limit = list_conditions["limit"]
            del list_conditions["limit"]

        if "skip" in list_conditions:
            skip = list_conditions["skip"]
            del list_conditions["skip"]

        if "order" in list_conditions:
            order = list_conditions["order"]
            del list_conditions["order"]

        limit = None if limit == 0 else limit
        try:
            conditions: list[Any] = self.__get_conditions(
                model_to_list, list_conditions, conjunction
            )

            conditions.extend(
                self.__get_join_conditions(model_to_list, join_conditions, conjunction)
            )

            join_models = [join_model for join_model in join_conditions]

            if date_range:
                conditions.append(
                    and_(
                        getattr(model_to_list, date_range.column_name)
                        >= date_range.from_date
                    )
                )
                conditions.append(
                    and_(
                        getattr(model_to_list, date_range.column_name)
                        <= date_range.to_date
                    )
                )

            if sum_by_column:
                sum_total = await self.get_model_sum(
                    model_to_list,
                    sum_by_column,
                    model_conditions=list_conditions,
                    date_range=date_range,
                    join_conditions=join_conditions,
                    conjunction=conjunction,
                )
            else:
                sum_total = None

            try:
                db_model_count = await self.get_model_count(
                    model_to_list,
                    count_by_column,
                    list_conditions,
                    date_range,
                    join_conditions=join_conditions,
                    conjunction=conjunction,
                )

                query: Select = select(model_to_list)

                for join_model in join_models:
                    query = query.join(join_conditions[join_model])

                model_list = await self.__make_query(
                    query,
                    model_to_list,
                    conditions,
                    order_by_column,
                    order,
                    skip,
                    limit,
                    conjunction,
                )

            except Exception as e:
                print(f"Captured exception log: {e}")
                db_model_count = 0
                model_list = []

            return {"items": model_list, "count": db_model_count, "sum": sum_total or 0}

        except AttributeError:
            raise HTTPException(
                status_code=403,
                detail=f"Invalid attribute for {model_to_list.__qualname__}",
            )

        except Exception as e:
            print(f"Captured exception log: {e}")
            raise HTTPException(
                status_code=404, detail=f"{model_to_list.__qualname__} not found"
            )

    async def search_model(
        self,
        model_to_search: Any,
        search: BaseModelSearch,
        order_by_column: str = "id",
        order: str = "asc",
        count_by_column: str = "id",
    ) -> dict[str, Any]:
        search_term: str = search.search_term
        search_columns: list[str] = search.search_fields
        join_search: list[JoinSearch] = search.join_search
        limit: int | None = search.limit
        skip: int = search.skip

        # We are using regular expressions to search for the search term in the columns
        limit = None if limit == 0 else limit

        search_conditions = []

        for column in search_columns:
            is_str_col: bool = (
                model_to_search.__table__.columns[column].type.python_type is str
            )
            if is_str_col:
                search_conditions.append(
                    getattr(model_to_search, column).ilike(f"%{search_term}%")
                )
            else:
                search_conditions.append(
                    cast(getattr(model_to_search, column), String).ilike(
                        f"%{search_term}%"
                    )
                )

        # querier = self.db.query(model_to_search)
        query: Select = select(model_to_search)

        joined_models: list[Any] = []

        for join_search_item in join_search:
            if join_search_item.model.__qualname__ not in joined_models:
                query = query.join(
                    join_search_item.model,
                    onclause=getattr(model_to_search, join_search_item.onkey)
                    == getattr(join_search_item.model, "uuid"),
                )

                joined_models.append(join_search_item.model.__qualname__)

            search_term = (
                f".*{search_term}.*"
                if " " not in search_term
                else f".*{search_term.replace(' ', '.*')}.*"
            )

            # append the condition to the search conditions, but also consider the `onkey`
            # parameter with will be used for `onclause`
            search_conditions.append(
                getattr(join_search_item.model, join_search_item.column).op("~*")(
                    search_term
                )
            )

        query = query.filter(or_(false(), *search_conditions))

        # Ordering
        if order != "asc":
            query = query.order_by(getattr(model_to_search, order_by_column).desc())
        else:
            query = query.order_by(getattr(model_to_search, order_by_column))

        # Pagination
        query = query.offset(skip).limit(limit)

        # Execution
        result: Result[Any] = await self.db.execute(query)
        model_list = result.unique().scalars().all()

        # Getting the count of total matching records
        count_query: Select = select(
            func.count(getattr(model_to_search, count_by_column))
        )
        count_result: Result[Any] = await self.db.execute(count_query)
        db_model_count = count_result.scalar_one()

        return {"items": model_list, "count": db_model_count}

    async def delete_model(
        self,
        model_to_delete: Any,
        delete_conditions: dict[str, Any] = {},
        autocommit: bool = True,
    ) -> dict[str, ActionStatus]:
        db_model = await self.get_model_or_404(
            model_to_get=model_to_delete,
            model_conditions=delete_conditions,
        )
        try:
            if autocommit:
                await self.__delete_and_commit(db_model)
                return {"status": ActionStatus.success}
            else:
                await self.__delete_no_commit(db_model)
                return {"status": ActionStatus.success}

        except Exception as e:
            print(f"Captured exception log: {e}")
            raise HTTPException(
                status_code=403,
                detail=f"Cannot delete this {model_to_delete.__qualname__}, "
                + "check if it's still in use",
            )

    async def ensure_unique(
        self,
        model_to_check: Any,
        unique_condition: dict[str, Any],
        custom_error: str = "",
    ) -> None:
        try:
            # try getting the model if it exists
            db_model = await self.get_model_or_404(
                model_to_get=model_to_check, model_conditions=unique_condition
            )

            # if it does raise an exception
            if db_model:
                if custom_error:
                    raise HTTPException(status_code=409, detail=custom_error)

                raise HTTPException(
                    status_code=409,
                    detail=f"{model_to_check.__qualname__} already exists",
                )

        except HTTPException as e:
            # 404 is expected if the model does not exist,
            # otherwise raise any other exception
            if e.status_code != 404:
                raise e

    async def model_exists(
        self,
        model_to_check: Any,
        model_conditions: dict[str, Any] = {},
        conjunction: str = "and",
    ) -> bool:
        try:
            result = await self.get_model_or_none(
                model_to_check, model_conditions, conjunction=conjunction
            )

            if result is not None:
                return True

            return False
        except Exception as e:
            print(f"Captured exception log: {e}")
            return False

    async def get_model_sum(
        self,
        model: Any,
        column_to_sum: str,
        model_conditions: dict[str, Any] = {},
        date_range: DateRange | None = None,
        join_conditions: dict[str, Any] = {},
        conjunction: str = "and",
    ) -> float:
        try:
            conditions: list[Any] = self.__get_conditions(
                model, model_conditions, conjunction
            )

            conditions.extend(
                self.__get_join_conditions(model, join_conditions, conjunction)
            )

            join_models = [join_model for join_model in join_conditions]

            if date_range:
                conditions.append(
                    and_(getattr(model, date_range.column_name) >= date_range.from_date)
                )
                conditions.append(
                    and_(getattr(model, date_range.column_name) <= date_range.to_date)
                )

            query: Select = select(func.sum(getattr(model, column_to_sum)))

            # todo: check if we don't need this
            for join_model in join_models:
                query = query.join(join_conditions[join_model])

            if conditions:
                if conjunction == "or":
                    query = query.filter(or_(false(), *conditions))
                    result: Result[Any] = await self.db.execute(query)
                    db_sum = result.one()
                else:
                    query = query.filter(and_(*conditions))
                    result: Result[Any] = await self.db.execute(query)
                    db_sum = result.one()

            else:
                query = query.filter(getattr(model, column_to_sum) != None)  # noqa
                result: Result[Any] = await self.db.execute(query)
                db_sum = result.one()

            db_sum = db_sum[0]
            if not db_sum:
                return float(0)
            return float(db_sum)

        except AttributeError:
            raise HTTPException(status_code=403, detail="Invalid server request")

        except Exception as e:
            print(f"Captured exception log: {e}")
            raise HTTPException(
                status_code=404,
                detail=f"Could not retrieve sum of {column_to_sum}. Record not found",
            )

    async def get_model_count(
        self,
        model_to_count: Any,
        column_to_count_by: str,
        model_conditions: dict[str, Any] = {},
        date_range: DateRange | None = None,
        join_conditions: dict[Any, Any] = {},
        conjunction: str = "and",
    ) -> int:
        try:
            conditions: list[Any] = self.__get_conditions(
                model_to_count, model_conditions, conjunction
            )

            conditions.extend(
                self.__get_join_conditions(model_to_count, join_conditions, conjunction)
            )

            join_models = [join_model for join_model in join_conditions]

            if date_range:
                conditions.append(
                    and_(
                        getattr(model_to_count, date_range.column_name)
                        >= date_range.from_date
                    )
                )

                conditions.append(
                    and_(
                        getattr(model_to_count, date_range.column_name)
                        <= date_range.to_date
                    )
                )

            query: Select = select(
                func.count(getattr(model_to_count, column_to_count_by))
            )

            # todo: check if we don't need this
            for join_model in join_models:
                query = query.join(join_conditions[join_model])

            if conditions:
                if conjunction == "or":
                    query = query.filter(or_(false(), *conditions))
                    result: Result[Any] = await self.db.execute(query)
                    db_count = result.one()
                else:
                    query = query.filter(and_(*conditions))
                    result: Result[Any] = await self.db.execute(query)
                    db_count = result.one()

            else:
                query = query.filter(
                    getattr(model_to_count, column_to_count_by) != None  # noqa
                )
                result: Result[Any] = await self.db.execute(query)
                db_count = result.one()

            db_count = db_count[0]

            if not db_count:
                return 0

            return int(db_count)

        except AttributeError:
            raise HTTPException(
                status_code=403,
                detail=f"Invalid attribute provided for {model_to_count.__qualname__}",
            )

        except Exception as e:
            print(f"Captured exception log: {e}")
            raise HTTPException(
                status_code=404,
                detail=f"Could not retrieve count of {column_to_count_by}. \
                    Record not found",
            )

    async def __add_and_commit(self, model_to_add: Any) -> None:
        # check if model to add is a list
        if isinstance(model_to_add, list):
            self.db.add_all(model_to_add)
        else:
            self.db.add(model_to_add)

        await self.db.commit()
        await self.db.refresh(model_to_add)

    async def __add_no_commit(self, model_to_add: Any) -> None:
        # check if model to add a list
        if isinstance(model_to_add, list):
            self.db.add_all(model_to_add)
        else:
            self.db.add(model_to_add)

        await self.db.flush()

    async def __update_and_commit(
        self, model_to_update: Any, update: BaseModel
    ) -> None:
        update_dict = self.__remove_invalid_fields(model_to_update, update)
        for key, value in update_dict.items():
            setattr(model_to_update, key, value)

        await self.db.commit()
        await self.db.refresh(model_to_update)

    async def __update_no_commit(self, model_to_update: Any, update: BaseModel) -> None:
        update_dict = self.__remove_invalid_fields(model_to_update, update)

        for key, value in update_dict.items():
            setattr(model_to_update, key, value)

        await self.db.flush()

    async def __delete_and_commit(self, model_to_delete: Any) -> None:
        await self.db.delete(model_to_delete)
        await self.db.commit()

    async def __delete_no_commit(self, model_to_delete: Any) -> None:
        await self.db.delete(model_to_delete)
        await self.db.flush()

    def __remove_invalid_fields(self, model: Any, data: BaseModel) -> dict[str, Any]:
        columns: set[str] = set(model.__table__.c.keys())
        data_fields: set[str] = set(data.model_dump(exclude_unset=True).keys())

        data_dict = data.model_dump(
            exclude=set(data_fields - columns),
            exclude_unset=True,
        )

        return data_dict

    def __get_conditions(
        self,
        model: Any,
        list_conditions: dict[str, Any],
        conjunction: str = "and",
    ) -> list[Any]:
        conditions: list[Any] = []
        for field_name in list_conditions:
            if list_conditions[field_name] is not None:
                if conjunction == "or":
                    conditions.append(
                        getattr(model, field_name) == list_conditions[field_name]
                    )
                else:
                    conditions.append(
                        and_(getattr(model, field_name) == list_conditions[field_name])
                    )
        return conditions

    def __get_join_conditions(
        self,
        model: Any,
        join_conditions: dict[Any, Any],
        conjunction: str = "and",
    ) -> list[Any]:
        join_models = [join_model for join_model in join_conditions]
        conditions: list[Any] = []
        for join_model in join_models:
            for field_name in join_conditions[join_model]:
                if join_conditions[join_model][field_name] is not None:
                    if conjunction == "or":
                        conditions.append(
                            getattr(join_model, field_name)
                            == join_conditions[join_model][field_name]
                        )
                    else:
                        conditions.append(
                            and_(
                                getattr(join_model, field_name)
                                == join_conditions[join_model][field_name]
                            )
                        )
        return conditions

    async def __make_query(
        self,
        query: Select,
        model: Any,
        conditions: list[Any],
        order_by_column: str,
        order: str,
        skip: int,
        limit: int | None,
        conjunction: str,
    ) -> Any:
        if conjunction == "or":
            if order != "asc":
                query = (
                    query.filter(or_(false(), *conditions))
                    .order_by(getattr(model, order_by_column).desc())
                    .offset(skip)
                    .limit(limit)
                )
            else:
                query = (
                    query.filter(or_(false(), *conditions))
                    .order_by(getattr(model, order_by_column).asc())
                    .offset(skip)
                    .limit(limit)
                )

            result: Result[Any] = await self.db.execute(query)
            return result.unique().scalars().all()

        else:
            if order != "asc":
                query = (
                    query.filter(and_(*conditions))
                    .order_by(getattr(model, order_by_column).desc())
                    .offset(skip)
                    .limit(limit)
                )
            else:
                query = (
                    query.filter(and_(*conditions))
                    .order_by(getattr(model, order_by_column).asc())
                    .offset(skip)
                    .limit(limit)
                )

            result: Result[Any] = await self.db.execute(query)
            return result.unique().scalars().all()

    def __result_or_404(
        self,
        query_result: Result[Any],
    ) -> Any:
        result = query_result.unique().scalars().first()
        if not result:
            raise HTTPException(status_code=404, detail="Not Found")

        return result

    def __result_or_none(
        self,
        query_result: Result[Any],
    ) -> Any:
        return query_result.unique().scalars().first()


@event.listens_for(AsyncSession.sync_session_class, "before_flush")
def receive_before_flush(
    session: Session, flush_context: Any, instances: list[Any]
) -> None:
    for instance in session.dirty:
        if hasattr(instance, "last_modified"):
            setattr(instance, "last_modified", func.now())
