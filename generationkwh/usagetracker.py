# -*- coding: utf-8 -*-

import datetime
import pytz

TZ = pytz.timezone('Europe/Madrid')

class UsageTracker(object):
    """UsageTracker manages the available use rights for a given partner.
    """
    def __init__(self, rights, usage, periodMask):
        self._rights = rights
        self._usage = usage
        self._periodMask = periodMask

    def available_kwh(self, member, start, end, fare, period):
        assert type(start) == datetime.date
        assert type(end) == datetime.date
        rights = self._rights.rights_kwh(member, start, end)
        periodMask = self._periodMask.periodMask(fare, period, start, end)
        usage = self._usage.usage(member, start, end)
        return int(sum(
            p-u if m else 0
            for p,u,m
            in zip(rights, usage, periodMask)
            ))

    def use_kwh(self, member, start, end, fare, period, kwh):
        allocated, usage_date_dict = self.use_kwh_with_dates_dict(member, start, end, fare, period, kwh)
        return allocated

    def use_kwh_with_dates_dict(self, member, start, end, fare, period, kwh):
        assert type(start) == datetime.date
        assert type(end) == datetime.date
        rights = self._rights.rights_kwh(member, start, end)
        periodMask = self._periodMask.periodMask(fare, period, start, end)
        usage = self._usage.usage(member, start, end)

        allocated = 0
        used_now =[]
        for i, (p, u, m) in enumerate(zip(rights, usage, periodMask)):
            if not m: continue # not in period
            used = int(min(kwh-allocated, p-u))
            usage[i] += used
            if used:
                used_now.append((i,used))
                allocated += used
                if kwh - allocated < 1:
                    break

        self._usage.updateUsage(member, start, usage)
        usage_date_dict = self.convert_usage_date_quantity(used_now, start, end)
        return allocated, usage_date_dict

    def refund_kwh(self, member, start, end, fare, period, kwh):
        assert type(start) == datetime.date
        assert type(end) == datetime.date
        rights = self._rights.rights_kwh(member, start, end)
        periodMask = self._periodMask.periodMask(fare, period, start, end)
        usage = self._usage.usage(member, start, end)

        deallocated = 0
        for i, (u, m) in reversed(list(enumerate(zip(usage, periodMask)))):
            if not m: continue # not in period
            unused = min(kwh-deallocated, u)
            usage[i] -= unused
            deallocated += unused

        self._usage.updateUsage(member, start, usage)
        return deallocated

    def usage(self, member, start, end):
        assert type(start) == datetime.date
        assert type(end) == datetime.date
        return self._usage.usage(member, start, end)

    def convert_usage_date_quantity(self, usage, start_date, end_date):
        def curveIndexToDate(start, index):
            """
                Maps an index withing an hourly curve starting at 'start' date
                into a local date.
                A day in houry curve has 25 positions. Padding is added
                to keep same solar time in the same position across summer
                daylight saving shift.
            """
            hoursPerDay = 25
            days = index//hoursPerDay
            resultday = start_date + datetime.timedelta(days=days)
            naiveday = datetime.datetime.combine(resultday, datetime.time(0,0,0))
            if naiveday.tzinfo is None:
                localday =  TZ.localize(naiveday)
            else:
                localday =  naiveday.astimezone(TZ)

            nextDay = TZ.normalize(localday + datetime.timedelta(days=1))
            toWinterDls = localday.dst() and not nextDay.dst()
            toSummerDls = not localday.dst() and nextDay.dst()

            hours = index%hoursPerDay
            if hours == 24 and not toWinterDls: return None
            if hours == 23 and toSummerDls: return None
            return TZ.normalize(localday+datetime.timedelta(hours=hours))

        result = {}
        for i, q in usage:
            current_date = curveIndexToDate(start_date, i)
            current_date_str = datetime.strptime(current_date, '%Y-%m-%d %H:%M:%S')
            result[current_date_str] = q

        return result


# vim: ts=4 sw=4 et
