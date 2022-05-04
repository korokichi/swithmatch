
import random
from math import ceil


# 勝敗決定時の勝ち点(ホントはここじゃないほうがいいけど……)


WIN,DRAW,LOSE = 3,1,0

class Player:

    def __init__(self,id,name) -> None:

        # プレイヤー基礎情報
        self.id = id
        self.name = name
        self.drop = False

        # 対戦履歴情報
        self.opponents_id = []  # 対戦相手履歴
        self.match_his = []     # 各ラウンドで得た勝ち点

        # 順位算定基準
        self.points = 0         # 合計勝ち点
        self.omw = None         # OMW%
        self.sowp = None        # 勝手累点
        self.avr_omw = None     # 平均OMW%

        # 重複回避用乱数
        self.rnd = 0

    # 対戦履歴の記録
    def mem_match(self,opponent,match_result):
        # 当ラウンドの対戦相手のID、対戦結果(インスタンス視点)、累計勝ち点を記録
        self.opponents_id.append(opponent.id)
        self.match_his.append(match_result)
        self.points = sum(self.match_his)

    # オポネント・マッチ・ウィン・パーセンテージの計算
    def cal_omw(self,players):

        # 現ラウンドまでに対戦した対戦相手を抽出
        opponents = list(filter(lambda player:player.id in self.opponents_id,players))
        
        ## 現在のラウンド
        #round_num = len(self.opponents_id)
        # 対戦相手別の合計勝ち数
        ops_wins = [op.match_his.count(WIN) for op in opponents]

        # 対戦相手ごとの最終勝率
        # 対戦相手の勝率が33%未満だった場合、その相手は勝率33%として扱う
        op_win_per = [op_win / len(op.match_his) if (op_win / len(op.match_his)) >= (1/3) 
                        else 1/3 for op_win,op in zip(ops_wins,opponents) ]
        
        # 対戦相手ごとの最終勝率を対戦人数で平均し、
        # オポネント・マッチ・ウィン・パーセンテージ算定
        omw = sum(op_win_per) / len(opponents)

        self.omw = omw
    
    # sowp:sum_opponents_win_point(勝手累点)の略
    def cal_sowp(self,players):

        # 現ラウンドまでに対戦した対戦相手を抽出
        opponents = list(filter(lambda player:
            player.id in self.opponents_id,
            players))

        # 対戦相手別の合計勝ち数
        ops_wins = [op.points for op in opponents]

        self.sowp = sum(ops_wins)

    def cal_avr_omw(self,players):

        # 現ラウンドまでに対戦した対戦相手を抽出
        opponents = list(filter(lambda player:player.id in self.opponents_id,players))
        op_omws = [op.omw for op in opponents]

        # 平均OMW%を算定
        self.avr_omw = sum(op_omws) / len(opponents)
    
    def set_drop(self):
        self.drop = True

# 各プレイヤーのOMW,勝手累点,平均OMWを計算
def cal_players_parameter(players):
    
    for pl in players:
        pl.cal_omw(players)
    
    for pl in players:
        pl.cal_sowp(players)
    
    for pl in players:
        pl.cal_avr_omw(players)

def sort_player(players):
    """
    点数、オポを考慮してソートする(順位算定)
    """
    cal_players_parameter(players)
    players.sort(key=lambda x:(x.drop,-x.points,-x.omw,-x.sowp,-x.avr_omw))

def cal_rand_seed(players):
    for pl in players:
        pl.rnd = random.random()

# 乱数で決めていく方
def cal_match_combination(players):
    
    # 重複が一番少なかった対戦組み合わせを採用
    min_dup = {'num':len(players),'seeds':None}

    for i in range(10000):
        # 初回は最初に決めた順位で組を決める
        if i != 0:
            cal_rand_seed(players)
            players.sort(key=lambda x:(x.drop,-x.points,x.rnd))
        
        match_num = ceil(sum([1 for pl in players if not pl.drop]) / 2)
        
        # 各マッチの処理
        # 対戦相手重複カウント
        cnt_dup = 0

        for j in range(1,match_num+1):

            # 対戦組み合わせ決定
            pl_a = players[2*j-2] 
            pl_b = players[2*j-1]

            if pl_b.id in pl_a.opponents_id:
                cnt_dup += 2
        
        # 生成したseed値でより小さい重複組合せが生成できたか確認
        min_dup['num'] = min(min_dup['num'],cnt_dup)

        # 重複人数の最小が更新できたら、seed値を保存
        if min_dup['num'] == cnt_dup:
            min_dup['seeds'] = [{'id':pl.id,'seed':pl.rnd} for pl in players]
    
        # 重複なしの組み合わせが見つかったらそれに決定
        if min_dup['num'] == 0:
            break
    
    # 算定したseed値をもとに組み合わせを確定
    for seed in min_dup['seeds']:
        found_pl=next( (pl for pl in players if pl.id==seed['id']) ,None)
        found_pl.rnd = seed['seed'] # type:ignore

# 対戦相手の履歴から決めていく方
def text_cal_match_combination(players):

    # 初期化
    com_match = [-1]*len(players)

    # 1000回トライしたらいけるやろの精神
    # 少なくとも1ラウンド2人までにできるはず？
    for t in range(1000):

        if t != 0:
            cal_rand_seed(players)
            players.sort(key=lambda x:(x.drop,-x.points,x.rnd))
        
        com_match = [-1]*len(players)
        
        for i in range(len(players)-1):
            
            if i not in com_match:
                
                # i+1~len(players)-1までで重複しない対戦可能な相手を検索
                for j in range(i+1,len(players)):

                    pl = players[i]
                    op_choice = players[j]

                    # すでに対戦相手が決まっている相手だったら次の候補へ
                    if j in com_match:
                        continue
                    # すでに対戦している相手だったら次の候補へ
                    elif op_choice.id in pl.opponents_id:
                        continue
                    # 対戦候補がドロップしてたら次の候補へ
                    elif op_choice.drop:
                        continue
                    
                    else:
                        com_match[i] = j
                        com_match[j] = i
                        break
        
        # ドロップしているプレイヤーの数を算定
        drop_player = sum([1 for pl in players if pl.drop])
        
        # 対戦相手が決まったプレイヤーの総数が、
        # ドロッププレイヤー＋Byeさんと当たった人(1名)以下なら、組分け確定
        if com_match.count(-1) <= drop_player + 1:
            
            """ for pl,next_op in zip(players,com_match):
                pl.opponents_id.append(next_op)
             """
            return com_match
    else:
        return com_match



def match(a:int,b:int) :
    a_c = random.random()
    b_c = random.random()

    # 引き分け確率
    draw_per = 0.05

    if random.random() < draw_per:
        return {a:DRAW,b:DRAW}

    # 引き分けでなかった場合
    if a_c >= b_c:
        return {a:WIN,b:LOSE}
    if a_c < b_c:
        return {a:LOSE,b:WIN}

# N,M= list(map(int, input().split()))

def main():
    N,M = 16,8

    TRIAL = 100
    cnt = 0
    # 対戦相手の平均重複数テスト
    for t in range(TRIAL):

        Players = [Player(i,f'player_{i}') for i in range(1,2*N+1)]

        #対戦結果作成
        for i in range(M):

            # 対戦相手の履歴から決めていく
            com_match = text_cal_match_combination(Players)

            for ai,a_op in enumerate(com_match):
                
                # 対戦相手のindexを決める
                b_op = com_match[a_op]
                
                # 対戦相手の数がマッチ数と一致してなく、dropもしてないなら
                # 処理が終わっていないplayerのため、対戦相手の確定処理を行う
                if len(Players[ai].opponents_id) != i+1 and not Players[ai].drop:

                    # aの対戦相手がbyeかつaがドロップしてないならaは不戦勝
                    # com_matchはすべてさらうので、b側の不戦勝処理も行われる
                    if a_op == -1 and not Players[i].drop:
                        Players[ai].opponents_id.append(-1)
                        a_r_point = WIN 
                        Players[ai].points += a_r_point
                        Players[ai].match_his.append(a_r_point)

                    # byeと当たっていないプレイヤー同士の場合、
                    # 通常の対戦処理を行う
                    if a_op != -1 and b_op != -1:
                        bi = a_op # bの対戦相手がbyeでなければ一意に定まる
                        pl_a = Players[ai] 
                        pl_b = Players[bi]

                        # 対戦結果
                        match_result:dict = match(pl_a.id,pl_b.id) # type:ignore

                        # 対戦履歴に関する情報を記録(player_a)
                        pl_a.opponents_id.append(pl_b.id)
                        a_r_point = match_result[pl_a.id]
                        pl_a.points += a_r_point
                        pl_a.match_his.append(a_r_point)

                        # 対戦履歴に関する情報を記録(player_a)
                        pl_b.opponents_id.append(pl_a.id)
                        b_r_point = match_result[pl_b.id]
                        pl_b.points += b_r_point
                        pl_b.match_his.append(b_r_point) 



            # 順位決定
            sort_player(Players)

            # ドロップ疑似実装
            Players[-(i+1)].drop = True

            dup_pl = []
            print(f'-------round{i+1}-------')
            for m,pl in enumerate(Players):
                if len(set(pl.opponents_id)) != len(pl.opponents_id):
                    # dup_pl.append((m,pl.id,pl.opponents_id[-1]))
                    dup_pl.append(f'順位:{m+1},勝ち点:{pl.points},id:{pl.id},対戦相手:{pl.opponents_id[-1]}')
            # print(dup_pl)
            for c in dup_pl:
                print(c)
            if i == M-1:
                cnt += len(dup_pl)

            # 経過表示用
            P_juni = [{'順位':i+1,'id':pl.id,
                        '勝ち点':pl.points,
                        'OMW%':pl.omw,
                        '勝手累点':pl.sowp,
                        '平均OMW%':pl.avr_omw,
                        'drop':pl.drop
                        }for i,pl in enumerate(Players)]
            pass
        

        pass

        # print('end')

    print(cnt/TRIAL)


if __name__ == '__main__':
    main()