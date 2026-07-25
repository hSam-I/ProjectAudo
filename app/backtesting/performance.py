class Performance:

    @staticmethod
    def win_rate(total, wins):

        if total == 0:
            return 0

        return wins / total * 100