def split_message(message, max_length=1000):
    """
    将长消息分割成多个短消息。
    每遇到一到两个换行符就进行分割，同时确保每条消息不超过最大长度。
    """
    parts = []
    current_part = ""
    lines = message.split('\n')

    for line in lines:
        if len(current_part) + len(line) + 1 > max_length:
            if current_part:
                parts.append(current_part.strip())
                current_part = ""
        
        current_part += line + '\n'

        if current_part.count('\n') >= 2:
            parts.append(current_part.strip())
            current_part = ""

    if current_part:
        parts.append(current_part.strip())

    return parts
