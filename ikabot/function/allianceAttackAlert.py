#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import time
import traceback
from ikabot.function.extracttable import parse_table

from ikabot.function.vacationMode import activateVacationMode
from ikabot.helpers.botComm import *
from ikabot.helpers.gui import enter
from ikabot.helpers.process import set_child_mode
from ikabot.helpers.signals import setInfoSignal
from ikabot.helpers.varios import daysHoursMinutes

t = gettext.translation(
    "allianceAttackAlert", localedir, languages=languages, fallback=True
)
_ = t.gettext


def allianceAttackAlert(session, event, stdin_fd, predetermined_input):
    """
    Parameters
    ----------
    session : ikabot.web.session.Session
    event : multiprocessing.Event
    stdin_fd: int
    predetermined_input : multiprocessing.managers.SyncManager.list
    """
    sys.stdin = os.fdopen(stdin_fd)
    config.predetermined_input = predetermined_input
    try:
        if checkTelegramData(session) is False:
            event.set()
            return

        banner()
        default = 20
        minutes = read(
            msg=_(
                "How often should I search for alliance attacks?(min:1, default: {:d}): "
            ).format(default),
            min=0,
            default=default,
        )
        # min_units = read(msg=_('Attacks with less than how many units should be ignored? (default: 0): '), digit=True, default=0)
        print(_("I will check for alliance attacks every {:d} minutes").format(minutes))
        enter()
    except KeyboardInterrupt:
        event.set()
        return

    set_child_mode(session)
    event.set()

    info = _("\nI check for alliance attacks every {:d} minutes\n").format(minutes)
    setInfoSignal(session, info)
    try:
        do_it(session, minutes)
    except Exception as e:
        msg = _("Error in:\n{}\nCause:\n{}").format(info, traceback.format_exc())
        sendToBot(session, msg)
    finally:
        session.logout()


def respondToAttack(session):
    """
    Parameters
    ---------
    session : ikabot.web.session.Session
    """

    # this allows the user to respond to an attack via telegram
    while True:
        time.sleep(60 * 3)
        responses = getUserResponse(session)
        for response in responses:
            # the response should be in the form of:
            # <pid>:<action number>
            rta = re.search(r"(\d+):?\s*(\d+)", response)
            if rta is None:
                continue

            pid = int(rta.group(1))
            action = int(rta.group(2))

            # if the pid doesn't match, we ignore it
            if pid != os.getpid():
                continue

            # currently just one action is supported
            if action == 1:
                # mv
                activateVacationMode(session)
            else:
                sendToBot(session, _("Invalid command: {:d}").format(action))


def do_it(session, minutes):
    """
    Parameters
    ----------
    session : ikabot.web.session.Session
    minutes : int
    """

    # this thread lets the user react to an attack once the alert is sent
    thread = threading.Thread(target=respondToAttack, args=(session,))
    thread.start()

    known_attack_end_dates = []
    while True:
        ##Catch errors inside the function to not exit for any reason.
        try:
            print("checking attacks")
            # get the militaryMovements
            html = session.get()

            city_id = re.search(r"currentCityId:\s(\d+),", html).group(1)
            url = "view=embassyGeneralAttacksToAlly&cityId=301772&position=10&backgroundView=city&currentCityId=301772&templateView=embassyGeneralAttacksToAlly&actionRequest=767a4dc7580c0485d5e3099c23b405d6&ajax=1"

            # url = 'view=militaryAdvisor&oldView=city&oldBackgroundView=city&backgroundView=city&currentCityId={}&actionRequest={}&ajax=1'.format(
            #     city_id, actionRequest)

            movements_response = session.post(url)
            # print("movements_response:" ,movements_response)
            postdata = json.loads(movements_response, strict=False)

            # with open("example.json", "w") as file:
            #     file.write(movements_response)
            # print("postdata:",postdata)
            
            attacks = parse_table(postdata[1][1][1])
            for attack in attacks:
                if attack["end_date"] in known_attack_end_dates:
                    continue
                known_attack_end_dates.append(attack["end_date"])
                sendToBot(session,f"ALERT !!!\n The Player {attack["attacker_name"]} ({attack["attacker_city_name"]}) \n {attack['active_action']} of {attack["ally_name"]} ({attack["ally_city_name"]}) with {attack["units"]} units , arriving in: {attack["period"]}")


        except Exception as e:
            info = _("\nI check for attacks every {:d} minutes\n").format(minutes)
            msg = _("Error in:\n{}\nCause:\n{}").format(info, traceback.format_exc())
            print(msg)
            # sendToBot(session, msg)

        time.sleep(minutes * 60)
