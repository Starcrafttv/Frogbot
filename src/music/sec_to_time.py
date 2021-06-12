def sec_to_time(sec):
    # Convert seconds to a normalized string
    m, s = divmod(round(sec), 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    if d > 1:
        if s < 10:
            s = f'0{s}'
        if m < 10:
            m = f'0{m}'
        return f'{d} days, {h}:{m}:{s}'
    elif d == 1:
        if s < 10:
            s = f'0{s}'
        if m < 10:
            m = f'0{m}'
        return f'{d} day, {h}:{m}:{s}'
    elif h > 0:
        if s < 10:
            s = f'0{s}'
        if m < 10:
            m = f'0{m}'
        return f'{h}:{m}:{s}'
    elif m > 0:
        if s < 10:
            s = f'0{s}'
        return f'{m}:{s}'
    else:
        return f'{s}'
