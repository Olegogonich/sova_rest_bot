from datetime import datetime, timedelta

import requests
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

import config as cf
from src.commands.server.util.db import user_tokens_db
from src.log import logger
from .text import *

router = Router(name=__name__)


report_types = {
    "revenue": "Выручка",
    "guests-checks": "Гости/чеки",
    "avg-check": "Средний чек",
    "write-off": "Списания",
    "food-cost": "Фудкост",
}


report_periods = {
    "last-day": "Вчерашний день",
    "this-week": "Текущая неделя",
    "this-month": "Текущий месяц",
    "this-year": "Текущий год",
    "last-week": "Прошлая неделя",
    "last-month": "Прошлый месяц",
    "last-year": "Прошлый год",
}


class FSMServerReportGet(StatesGroup):
    ask_report_type = State()
    ask_report_period = State()


def request_get_reports(token: str, report_type: str, period: str) -> dict | None:
    today = datetime.now(tz=cf.TIMEZONE).date()

    match period:
        case "last-day":
            date_from = today - timedelta(days=1)
            date_to = date_from
        case "this-week":
            date_from = today - timedelta(days=today.weekday())
            date_to = today
        case "this-month":
            date_from = today.replace(day=1)
            date_to = today
        case "this-year":
            date_from = today.replace(day=1, month=1)
            date_to = today
        case "last-week":
            date_from = today - timedelta(days=today.weekday()+7)
            date_to = today - timedelta(days=today.weekday()+1)
        case "last-month":
            date_from = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            date_to = today.replace(day=1) - timedelta(days=1)
        case "last-year":
            date_from = (today.replace(day=1, month=1) - timedelta(days=1)).replace(day=1, month=1)
            date_to = today.replace(day=1, month=1) - timedelta(days=1)
        case _:
            logger.msg("ERROR", f"Error SendReports UnknownReportPeriod: {period=}")
            return None

    req = requests.post(
        url=f"{cf.API_PATH}/api/{report_type}",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "dateFrom": date_from.isoformat(),
            "dateTo": date_to.isoformat()
        }
    )
    if req.status_code != 200:
        logger.msg("ERROR", f"Error RequestGetReports: {req.text}\n{report_type=} {period=} {token=}")
        return None
    return req.json()


@router.callback_query(F.data == "server_report_get")
async def choose_report_type(query: CallbackQuery, state: FSMContext):
    await state.clear()
    kb = IKM(inline_keyboard=[
        [IKB(text=v, callback_data=k)] for k, v in report_types.items()
    ])
    await state.set_state(FSMServerReportGet.ask_report_type)
    await query.message.answer("Выберите вид отчёта", reply_markup=kb)
    await query.answer()


@router.callback_query(FSMServerReportGet.ask_report_type)
async def choose_report_period(query: CallbackQuery, state: FSMContext):
    await state.update_data({'report_type': query.data})

    kb = IKM(inline_keyboard=[
        [IKB(text=v, callback_data=k)] for k, v in report_periods.items()
    ])
    await state.set_state(FSMServerReportGet.ask_report_period)
    await query.message.edit_text("Выберите период отчёта", reply_markup=kb)
    await query.answer()


@router.callback_query(FSMServerReportGet.ask_report_period)
async def send_reports(query: CallbackQuery, state: FSMContext):
    await query.message.edit_text("Загрузка... ⚙️<i>\nМожет занять несколько минут</i>")
    await query.answer()

    user_id = query.from_user.id
    token = user_tokens_db.get_token(user_id)
    report_type = (await state.get_data()).get('report_type')
    report_period = query.data

    await state.clear()

    logger.info(f"SendReport: {user_id=} {report_type=} {report_period=} {token=}")

    data = request_get_reports(token, report_type, report_period)

    if data is None:
        await query.message.edit_text("Ошибка")
        return

    if len(data.get('report')) == 0:
        await query.message.edit_text("Не удалось составить отчёт")
        return

    text = ""
    for report in data.get('report'):
        match report_type:
            case "revenue":
                text += report_revenue_text(report)
            case "guests-checks":
                text += report_guests_checks_text(report)
            case "avg-check":
                text += report_avg_check_text(report)
            case "write-off":
                text += report_write_off_text(report)
            case "food-cost":
                text += report_food_cost_text(report)
            case _:
                logger.msg("ERROR", f"Error SendReports UnknownReportType: {report_type=}")
                await query.message.answer("Ошибка")
                return
        text += "\n\n\n"

    kb = IKM(inline_keyboard=[[IKB(text='В меню отчётов ↩️', callback_data='report_menu')]])
    await query.message.answer(text, reply_markup=kb)

    logger.info(f"SendReport: Success {user_id=}")
    await query.message.edit_text(f"<i>Отчёт: <b>{report_types.get(report_type)}</b> за {report_periods.get(report_period)}:</i> 👇")


# @router.message(Command('server_get_report'))
# async def get_report(msg: Message):
#     database = db.user_tokens_db
#     token = database.get_token(tgid=str(msg.from_user.id))
#
#     loading_msg = await msg.answer("...")
#
#     req = await send_request_to_get_reports(token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiIxIiwic2x1ZyI6IlJPR0FMSUsiLCJpYXQiOjE3MzM3NTMzOTgsImV4cCI6MTczMzgzOTc5OH0.LtUIvj0WHrLRw9D3IMOBdPOuKatIqOyYnVm3D760dsA")
#
#     if req.status_code != 200:
#         await loading_msg.edit_text(f"Error: {req.status_code}")
#         return
#
#     text = ""
#     for rep in req.json()['report']:
#         text += f"\n{rep}\n"
#
#     await loading_msg.edit_text(text)

