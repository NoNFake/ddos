from . import ddos
import os

preview = """
    -t <target_url> -tr <thread_count> -n <sleep_time>


"""

menu = f"""

  - http -
[t] target_url: 
[n] sleep_time:
[tr] thread_count:


  - udp/tcp -


[u] update

"""



def main():
    print(menu)

    choose = input("> ")

    if choose == "t":
        target_url = input("target_url: ")
        print(f"Target URL set to: {target_url}")
    if choose == "u":
        # ddos.update_tool()
        os.system("git pull && uv run -m ddos")



if __name__ == "__main__":
    # ddos.main()   
    main()
