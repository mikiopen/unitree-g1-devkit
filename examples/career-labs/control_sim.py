"""Independent single-joint PD simulation. These gains are not G1 parameters."""
import argparse, csv, json, math
from pathlib import Path


def simulate(kp=20,kd=4,dt=0.002,duration=3):
    if not all(math.isfinite(value) for value in (kp,kd,dt,duration)) or not (0<kp<=1000 and 0<=kd<=100 and 0.0001<=dt<=0.01 and dt<=duration<=30):
        raise ValueError('Invalid simulation parameters')
    q=dq=0.0; rows=[]
    for step in range(int(duration/dt)):
        # Unit inertia, viscous damping 0.2, bounded educational torque +/- 5.
        torque=max(-5,min(5,kp*(1-q)-kd*dq))
        dq+=(torque-0.2*dq)*dt; q+=dq*dt
        rows.append((step*dt,q,dq,torque))
    return rows,{'model':'unit inertia + damping 0.2','target_rad':1,
                 'final_error_rad':abs(1-q),'overshoot_rad':max(0,max(row[1] for row in rows)-1),
                 'rmse_rad':math.sqrt(sum((1-row[1])**2 for row in rows)/len(rows)),'source':'simulation'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--kp',type=float,default=20); parser.add_argument('--kd',type=float,default=4); parser.add_argument('--output',type=Path)
    args=parser.parse_args(); rows,metrics=simulate(args.kp,args.kd)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('x',newline='',encoding='utf-8') as stream:
            writer=csv.writer(stream); writer.writerow(('time_s','q_rad','dq_rad_s','torque')); writer.writerows(rows)
    print(json.dumps(metrics,indent=2))
