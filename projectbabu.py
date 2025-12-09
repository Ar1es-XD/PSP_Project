import random
y = input()
wanted = list(y)
alp="abcdefghijklmnopqrstuvwxyz"
cur = [random.choice(alp) for u in range(len(wanted))]
tries = 0
def get_ran_ch():
    return random.choice(alp)
while cur!=wanted:
    tries+=1
    for i in range(len(wanted)):
        if cur[i] != wanted[i]:
            cur[i] = get_ran_ch()
        
    print(f"attempt {tries}:{''.join(cur)}")
print("\n password evolved succesfully")
print(f"target word:{''.join(wanted)}")
print(f"total attempts :{tries}")