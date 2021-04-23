from siyu import db


def save_check(object):
    try:
        db.session.add(object)
        db.session.commit()
        return False
    except Exception as ex:
        db.session.rollback()
        return str(ex)


def update_check():
    try:
        db.session.commit()
        return False
    except Exception as ex:
        db.session.rollback()
        return str(ex)
