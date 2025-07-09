KEEP_DAYS = 7
CREATE_TABLE = """
               CREATE TABLE IF NOT EXISTS message
               (
                   user_id
                   BIGINT
                   NOT
                   NULL,
                   message_date
                   DATE
                   NOT
                   NULL,
                   message_count
                   INT
                   NOT
                   NULL
                   DEFAULT
                   0,
                   PRIMARY
                   KEY
               (
                   user_id,
                   message_date
               )
                   ); 
               """

DATABASE_DESIGN = {
    # is_ban
    # user_id
    # chat_id
    # total_bans
    # reason
    # ban_date
    # who_banned
    # record_number_of_bans_in_a_month
    # last_ban_date
    #
}