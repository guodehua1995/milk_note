# 随机打乱字符串
import random

def shuffle_string(s: str) -> str:
    s_list = list(s)
    random.shuffle(s_list)
    return ''.join(s_list)

if __name__ == "__main__":
    print(shuffle_string("再一次证明中文顺序不影响阅读"))
