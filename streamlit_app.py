from itertools import product

import plotly.graph_objects as go
import streamlit as st


st.set_page_config(page_title="쌓기나무 탐정단", page_icon="🧱", layout="wide")
st.markdown(
    """
    <style>
    .stApp { background: #fffaf2; color: #49382d; }
    h1, h2, h3 { color: #70452f; }
    [data-testid="stHeader"] { background: rgba(255, 250, 242, 0.9); }
    [data-baseweb="tab-list"] { gap: 0.6rem; }
    [data-baseweb="tab"] {
        background: #fff1d6; border-radius: 14px 14px 0 0;
        color: #70452f; padding: 0.65rem 1rem;
    }
    [data-baseweb="tab"][aria-selected="true"] {
        background: #ffd58a; color: #57351f; font-weight: 700;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #fffdf8; border-color: #f0dfc7; border-radius: 18px;
    }
    .stButton > button {
        background: #fff1d6; border: 1px solid #efc98b;
        border-radius: 14px; color: #5b4030; min-height: 2.7rem;
    }
    .stButton > button:hover { background: #ffe1aa; border-color: #df9d4c; color: #4a2d1c; }
    .stButton > button[kind="primary"] {
        background: #ef8f62; border-color: #df784e; color: white;
    }
    [data-testid="stAlert"] { border-radius: 16px; }
    </style>
    """,
    unsafe_allow_html=True,
)

EMPTY = ((0, 0), (0, 0))
ALL_MODELS = tuple(((values[0], values[1]), (values[2], values[3])) for values in product(range(3), repeat=4))
FRONT = "앞"
LEFT = "왼쪽"
RIGHT = "오른쪽"
TOP = "위"


def block_count(model):
    return sum(sum(row) for row in model)


def projection(model, direction):
    if direction == TOP:
        return tuple(tuple(int(height > 0) for height in row) for row in reversed(model))
    if direction == FRONT:
        return tuple(max(model[0][column], model[1][column]) for column in range(2))
    if direction == LEFT:
        return tuple(max(model[row][0], model[row][1]) for row in (1, 0))
    if direction == RIGHT:
        return tuple(max(model[row][0], model[row][1]) for row in (0, 1))
    raise ValueError(f"알 수 없는 방향: {direction}")


def diagram_text(pattern, direction):
    if direction == TOP:
        rows = pattern
        return "  \n".join("".join("🟧" if occupied else "⬜" for occupied in row) for row in rows)
    return "  \n".join(
        "".join("🟧" if pattern[column] >= level else "⬜" for column in range(2))
        for level in (2, 1)
    )


def diagram_html(pattern, direction):
    if direction == TOP:
        rows = pattern
        cells = [occupied for row in rows for occupied in row]
    else:
        cells = [pattern[column] >= level for level in (2, 1) for column in range(2)]
    squares = "".join(
        f'<div style="width:42px;height:42px;background:{"#ff9b54" if filled else "#fff8ec"};'
        'border:2px solid #76543d;box-sizing:border-box"></div>'
        for filled in cells
    )
    return (
        f'<div aria-label="{direction}에서 본 모양" '
        'style="display:grid;grid-template-columns:repeat(2,42px);width:84px;'
        f'border:2px solid #76543d;border-radius:6px;overflow:hidden">{squares}</div>'
    )


def side_patterns():
    return tuple(product(range(3), repeat=2))


def top_patterns():
    return tuple(
        ((bits[0], bits[1]), (bits[2], bits[3]))
        for bits in product((0, 1), repeat=4)
    )


def find_models(clues):
    return tuple(
        model for model in ALL_MODELS
        if all(projection(model, direction) == pattern for direction, pattern in clues.items())
    )


def has_game_solution_with_matching_top(model_a):
    target_top = projection(model_a, TOP)
    return any(
        projection(candidate, FRONT) == (2, 2)
        and projection(candidate, RIGHT) == (2, 2)
        and projection(candidate, TOP) == target_top
        and block_count(candidate) != block_count(model_a)
        for candidate in ALL_MODELS
    )


def make_figure(model, camera="initial"):
    fig = go.Figure()
    face_colors = [
        "#ff6b5e", "#ffbf3f", "#14b889", "#4d83f2",
        "#f05c9c", "#8c5ce8", "#00a9d6", "#f07835",
    ]
    fig.add_trace(go.Mesh3d(
        x=[0, 2, 2, 0],
        y=[0, 0, 2, 2],
        z=[-0.04] * 4,
        i=[0, 0],
        j=[1, 2],
        k=[2, 3],
        color="#d8b27c",
        flatshading=True,
        hoverinfo="skip",
        showscale=False,
    ))
    board_x, board_y, board_z = [], [], []
    for coordinate in range(3):
        board_x.extend((coordinate, coordinate, None, 0, 2, None))
        board_y.extend((0, 2, None, coordinate, coordinate, None))
        board_z.extend((-0.02, -0.02, None, -0.02, -0.02, None))
    edge_x, edge_y, edge_z = [], [], []
    for row in range(2):
        for column in range(2):
            for level in range(model[row][column]):
                x, y, z = column, row, level
                vertices = [
                    (x, y, z), (x + 1, y, z), (x + 1, y + 1, z), (x, y + 1, z),
                    (x, y, z + 1), (x + 1, y, z + 1),
                    (x + 1, y + 1, z + 1), (x, y + 1, z + 1),
                ]
                triangles = [
                    (0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
                    (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
                    (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7),
                ]
                fig.add_trace(go.Mesh3d(
                    x=[vertex[0] for vertex in vertices],
                    y=[vertex[1] for vertex in vertices],
                    z=[vertex[2] for vertex in vertices],
                    i=[triangle[0] for triangle in triangles],
                    j=[triangle[1] for triangle in triangles],
                    k=[triangle[2] for triangle in triangles],
                    color=face_colors[row * 2 + column + level * 4],
                    flatshading=True,
                    hoverinfo="skip",
                    showscale=False,
                    lighting=dict(ambient=0.8, diffuse=0.55, specular=0.12, roughness=0.8),
                ))
                for start, end in (
                    (0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6),
                    (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7),
                ):
                    edge_x.extend((vertices[start][0], vertices[end][0], None))
                    edge_y.extend((vertices[start][1], vertices[end][1], None))
                    edge_z.extend((vertices[start][2], vertices[end][2], None))

    fig.add_trace(go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z, mode="lines",
        line=dict(color="#49382d", width=3), hoverinfo="skip", showlegend=False,
    ))
    fig.add_trace(go.Scatter3d(
        x=board_x, y=board_y, z=board_z, mode="lines",
        line=dict(color="#805b32", width=3), hoverinfo="skip", showlegend=False,
    ))
    fig.add_trace(go.Scatter3d(
        x=[0.35, 0.35], y=[-0.18, -0.75], z=[0.04, 0.04],
        mode="lines+text", text=["", "앞"], textposition="bottom center",
        line=dict(color="#d53f3f", width=7), textfont=dict(color="#c53030", size=14),
        hoverinfo="skip", showlegend=False,
    ))
    cameras = {
        "initial": dict(eye=dict(x=2.7, y=-3.3, z=2.8)),
        FRONT: dict(eye=dict(x=0.05, y=-4.5, z=1.5)),
        LEFT: dict(eye=dict(x=-4.5, y=0.05, z=1.5)),
        RIGHT: dict(eye=dict(x=4.5, y=0.05, z=1.5)),
        TOP: dict(eye=dict(x=0.05, y=-0.05, z=5)),
    }
    fig.update_layout(
        height=370,
        margin=dict(l=0, r=0, t=5, b=0),
        showlegend=False,
        scene=dict(
            xaxis=dict(visible=False, range=[-0.3, 2.3]),
            yaxis=dict(visible=False, range=[-1.0, 2.3]),
            zaxis=dict(visible=False, range=[-0.3, 2.6]),
            aspectmode="data",
            camera=cameras[camera],
        ),
    )
    return fig


def show_model(model, key, camera_key):
    st.plotly_chart(
        make_figure(model, st.session_state.get(camera_key, "initial")),
        key=key,
        config={"displayModeBar": False, "scrollZoom": True, "responsive": True},
        use_container_width=True,
    )
    controls = st.columns(5)
    for column, (label, view) in zip(controls, (
        ("앞", FRONT), ("왼쪽", LEFT), ("오른쪽", RIGHT), ("위", TOP), ("처음 시점", "initial")
    )):
        with column:
            st.button(
                label,
                key=f"{key}_{view}_camera",
                on_click=set_camera,
                args=(camera_key, view),
                use_container_width=True,
            )


def set_camera(key, view):
    st.session_state[key] = view


def show_diagram(pattern, direction, caption=None):
    if caption:
        st.caption(caption)
    st.markdown(diagram_html(pattern, direction), unsafe_allow_html=True)


def set_height(state_key, history_key, index, change):
    model = [list(row) for row in st.session_state[state_key]]
    row, column = divmod(index, 2)
    updated = model[row][column] + change
    if not 0 <= updated <= 2:
        return
    st.session_state[history_key].append(st.session_state[state_key])
    model[row][column] = updated
    st.session_state[state_key] = tuple(tuple(values) for values in model)


def undo_height(state_key, history_key):
    if st.session_state[history_key]:
        st.session_state[state_key] = st.session_state[history_key].pop()


def initialize_model_state(state_key, history_key):
    st.session_state.setdefault(state_key, EMPTY)
    st.session_state.setdefault(history_key, [])


def editor_controls(state_key, history_key, widget_prefix):
    options = ["앞-왼쪽 칸", "앞-오른쪽 칸", "뒤-왼쪽 칸", "뒤-오른쪽 칸"]
    selected = st.selectbox("블록을 놓을 칸", options, key=f"{widget_prefix}_cell")
    index = options.index(selected)
    row, column = divmod(index, 2)
    current_height = st.session_state[state_key][row][column]
    add_col, remove_col, undo_col = st.columns(3)
    with add_col:
        st.button(
            "블록 놓기", key=f"{widget_prefix}_add", disabled=current_height >= 2,
            on_click=set_height, args=(state_key, history_key, index, 1), use_container_width=True,
        )
    with remove_col:
        st.button(
            "맨 위 블록 빼기", key=f"{widget_prefix}_remove", disabled=current_height <= 0,
            on_click=set_height, args=(state_key, history_key, index, -1), use_container_width=True,
        )
    with undo_col:
        st.button(
            "한 단계 되돌리기", key=f"{widget_prefix}_undo",
            disabled=not st.session_state[history_key],
            on_click=undo_height, args=(state_key, history_key), use_container_width=True,
        )


def select_diagram(label, direction, key):
    patterns = top_patterns() if direction == TOP else side_patterns()
    st.markdown(f"**{label}**")
    st.caption("그림을 눌러 골라요. 주황색 칸이 보이는 블록이에요.")
    selected = st.session_state.setdefault(key, patterns[0])
    columns_per_row = 4 if direction == TOP else 3
    columns = st.columns(columns_per_row)
    for index, pattern in enumerate(patterns):
        with columns[index % columns_per_row]:
            st.button(
                diagram_text(pattern, direction),
                key=f"{key}_option_{index}",
                type="primary" if pattern == selected else "secondary",
                help="이 모양 선택",
                on_click=set_diagram_selection,
                args=(key, pattern),
                use_container_width=True,
            )
    st.caption("지금 고른 모양")
    show_diagram(selected, direction)
    return selected


def set_diagram_selection(key, pattern):
    st.session_state[key] = pattern


def draw_clues(clues, title="선택한 그림"):
    st.markdown(f"**{title}**")
    columns = st.columns(max(1, len(clues)))
    for column, (direction, pattern) in zip(columns, clues.items()):
        with column:
            show_diagram(pattern, direction, f"{direction}에서 본 모양")


def render_search_tab():
    st.subheader("방향별 그림을 골라 같은 모형을 찾아봐요")
    st.write("각 칸의 높이는 0~2층이에요. 위에서 본 그림은 바닥 칸의 점유 여부를 나타내요.")
    left_col, right_col, top_col = st.columns(3)
    with left_col:
        left = select_diagram("왼쪽에서 본 모양", LEFT, "search_left")
    with right_col:
        right = select_diagram("오른쪽에서 본 모양", RIGHT, "search_right")
    with top_col:
        top = select_diagram("위에서 본 모양", TOP, "search_top")
    front_enabled = st.checkbox("앞에서 본 모양을 추가 단서로 사용하기")
    front = select_diagram("앞에서 본 모양", FRONT, "search_front") if front_enabled else None
    clues = {LEFT: left, RIGHT: right, TOP: top}
    if front_enabled:
        clues[FRONT] = front

    if st.button("가능한 모형 찾기", type="primary", key="find_models"):
        st.session_state.search_clues = clues
        st.session_state.search_results = find_models(clues)
        st.session_state.search_index = 0

    if "search_results" not in st.session_state:
        return
    st.divider()
    saved_clues = st.session_state.get("search_clues", clues)
    draw_clues(saved_clues, "결과를 찾을 때 사용한 단서")
    results = st.session_state.search_results
    if not results:
        st.warning("이 그림들을 모두 만족하는 모형은 없어요")
        if LEFT in saved_clues and RIGHT in saved_clues and saved_clues[LEFT] != tuple(reversed(saved_clues[RIGHT])):
            st.info("건물의 반대편에서 보면 그림의 좌우가 바뀌어요")
        return
    st.success(f"조건을 만족하는 모형은 모두 {len(results)}개예요.")
    index = st.session_state.search_index
    previous, count_col, next_col = st.columns([1, 2, 1])
    with previous:
        st.button(
            "이전 모형", key="previous_model", disabled=index == 0,
            on_click=move_model_index, args=(-1,), use_container_width=True,
        )
    with count_col:
        st.markdown(f"<div style='text-align:center;padding:8px'>모형 {index + 1} / {len(results)}</div>", unsafe_allow_html=True)
    with next_col:
        st.button(
            "다음 모형", key="next_model", disabled=index >= len(results) - 1,
            on_click=move_model_index, args=(1,), use_container_width=True,
        )
    show_model(results[index], "search_result_3d", "search_camera")


def move_model_index(change):
    st.session_state.search_index = min(
        max(0, st.session_state.search_index + change),
        len(st.session_state.search_results) - 1,
    )


def render_make_tab():
    initialize_model_state("free_model", "free_history")
    st.subheader("빈 바닥판에서 나만의 건물을 지어요")
    st.caption("바닥은 2×2이고, 한 칸에는 최대 두 층까지 쌓을 수 있어요.")
    editor_controls("free_model", "free_history", "free")
    reset_col, count_col = st.columns(2)
    with reset_col:
        st.button(
            "처음부터", key="free_reset",
            on_click=reset_model, args=("free_model", "free_history"),
            use_container_width=True,
        )
    with count_col:
        if st.button("전체 개수 확인", key="free_count", use_container_width=True):
            st.session_state.free_count_visible = True
    if st.session_state.get("free_count_visible"):
        st.info(f"쌓인 블록은 모두 {block_count(st.session_state.free_model)}개예요.")
    show_model(st.session_state.free_model, "free_3d", "free_camera")

    if st.button("방향별 그림 확인", key="free_show_views"):
        st.session_state.free_views_visible = True
    if st.session_state.get("free_views_visible"):
        st.markdown("**내 건물을 방향별로 보면**")
        columns = st.columns(4)
        for column, direction in zip(columns, (FRONT, LEFT, RIGHT, TOP)):
            with column:
                show_diagram(projection(st.session_state.free_model, direction), direction, f"{direction}에서 본 모양")


def reset_model(state_key, history_key):
    st.session_state[state_key] = EMPTY
    st.session_state[history_key] = []


def reset_game():
    st.session_state.game_stage = 1
    st.session_state.game_a = None
    st.session_state.game_a_work = EMPTY
    st.session_state.game_a_history = []
    st.session_state.game_b = EMPTY
    st.session_state.game_b_history = []
    st.session_state.game_answer = ""
    st.session_state.game_report_submitted = False
    st.session_state.game_a_feedback = ""
    st.session_state.game_b_feedback = ""


def check_game_a():
    model = st.session_state.game_a_work
    incorrect = [
        direction for direction in (FRONT, RIGHT)
        if projection(model, direction) != (2, 2)
    ]
    if incorrect:
        st.session_state.game_a_feedback = "다시 확인할 방향: " + "·".join(incorrect)
        return
    st.session_state.game_a = model
    st.session_state.game_b = EMPTY
    st.session_state.game_b_history = []
    st.session_state.game_stage = 2
    st.session_state.game_a_feedback = ""


def check_game_b(stage):
    model_a = st.session_state.game_a
    model_b = st.session_state.game_b
    incorrect = [
        direction for direction in (FRONT, RIGHT)
        if projection(model_b, direction) != (2, 2)
    ]
    if incorrect:
        st.session_state.game_b_feedback = "다시 확인할 방향: " + "·".join(incorrect)
        return
    if block_count(model_a) == block_count(model_b):
        st.session_state.game_b_feedback = "두 건물의 블록 수가 같아요. 블록 수를 다르게 해 보세요."
        return
    if stage == 2:
        st.session_state.game_stage = (
            4 if projection(model_a, TOP) == projection(model_b, TOP) else 3
        )
        st.session_state.game_b_feedback = ""
        return
    if projection(model_a, TOP) == projection(model_b, TOP):
        st.session_state.game_stage = 4
        st.session_state.game_b_feedback = ""
        return
    st.session_state.game_b_feedback = "위에서 본 점유 칸이 달라요. 앞·오른쪽 그림과 블록 수 차이도 유지해 다시 살펴보세요."


def render_game_tab():
    st.subheader("탐정 게임: 같은 사진, 다른 건물")
    st.info("두 건물의 사진이 똑같아요. 하지만 공사 기록에는 사용한 블록 수가 다르다고 적혀 있어요. 탐정이 되어 두 건물을 직접 만들고 기록이 맞는지 확인해 주세요!")
    stage = st.session_state.game_stage
    if stage == 3 and projection(st.session_state.game_a, TOP) == projection(st.session_state.game_b, TOP):
        st.session_state.game_stage = 4
        stage = 4
    st.progress(min(stage, 4) / 4, text=f"진행 단계 {min(stage, 3)} / 3")

    if stage == 1:
        initialize_model_state("game_a_work", "game_a_history")
        st.markdown("### 1단계 · 첫 번째 건물 복원")
        st.write("단서: **앞과 오른쪽에서 보면 모두 2×2 격자가 꽉 차 있어요.**")
        show_diagram((2, 2), FRONT, "앞에서 본 단서")
        show_diagram((2, 2), RIGHT, "오른쪽에서 본 단서")
        editor_controls("game_a_work", "game_a_history", "game_a")
        show_model(st.session_state.game_a_work, "game_a_work_3d", "game_a_camera")
        st.button("검사하기", key="check_game_a", type="primary", on_click=check_game_a)
        if st.session_state.get("game_a_feedback"):
            st.warning(st.session_state.game_a_feedback)
        return

    st.markdown("### 1단계 · 첫 번째 건물 복원 ✓")
    st.success(f"건물 A를 저장했어요. 블록 {block_count(st.session_state.game_a)}개")
    if stage == 2:
        st.markdown("### 2단계 · 두 번째 건물 찾기")
        st.write("건물 B도 앞·오른쪽 그림은 같아야 해요. 하지만 전체 블록 수는 건물 A와 달라야 해요.")
    elif stage == 3:
        st.markdown("### 3단계 · 위에서 봐도 같은가?")
        st.write("건물 A와 B의 위에서 본 점유 칸을 같게 만들어요. 앞·오른쪽 그림과 블록 수 차이도 유지해 주세요.")
        if projection(st.session_state.game_a, TOP) == projection(st.session_state.game_b, TOP):
            st.success("두 건물은 위에서 본 점유 칸도 같아요!")
        elif not has_game_solution_with_matching_top(st.session_state.game_a):
            st.warning("현재 건물 A로는 조건을 모두 만족하는 건물 B가 없어요. 건물 A를 다시 설계해 주세요.")
            if st.button("건물 A 다시 설계하기", key="redesign_a", type="primary"):
                st.session_state.game_stage = 1
                st.session_state.game_a = None
                st.session_state.game_b_feedback = ""
                st.session_state.game_a_work = EMPTY
                st.session_state.game_a_history = []
            return

    if stage in (2, 3):
        initialize_model_state("game_b", "game_b_history")
        editor_controls("game_b", "game_b_history", "game_b")
        show_model(st.session_state.game_b, "game_b_3d", "game_b_camera")
        button_label = "검사하기" if stage == 2 else "위에서 본 모양 확인"
        st.button(
            button_label, key=f"check_game_b_{stage}", type="primary",
            on_click=check_game_b, args=(stage,),
        )
        if st.session_state.get("game_b_feedback"):
            st.warning(st.session_state.game_b_feedback)
        if stage == 3 and projection(st.session_state.game_a, TOP) == projection(st.session_state.game_b, TOP):
            if st.button("같은 점유 칸으로 통과하기", key="accept_same_top"):
                st.session_state.game_stage = 4
        return

    st.markdown("### 사건 기록")
    col_a, col_b = st.columns(2)
    for column, label, model, key, camera_key in (
        (col_a, "건물 A", st.session_state.game_a, "game_final_a", "game_a_final_camera"),
        (col_b, "건물 B", st.session_state.game_b, "game_final_b", "game_b_final_camera"),
    ):
        with column:
            st.markdown(f"#### {label} · 블록 {block_count(model)}개")
            show_model(model, key, camera_key)
            show_diagram(projection(model, TOP), TOP, "위에서 본 모양")
    st.markdown("**어느 칸의 층수가 다른가요? 그런데 왜 방향별 그림은 그대로였나요?**")
    st.text_area("탐정 보고서", key="game_answer", placeholder="생각한 내용을 자유롭게 적어 보세요.")
    if st.button("보고서 제출", key="submit_report", type="primary", disabled=not st.session_state.game_answer.strip()):
        st.session_state.game_report_submitted = True
    if st.session_state.get("game_report_submitted"):
        st.success("🏅 사건 해결!")
    st.button("게임 다시 시작", key="restart_game", on_click=reset_game)


def initialize_session():
    st.session_state.setdefault("game_stage", 1)
    st.session_state.setdefault("game_a", None)
    st.session_state.setdefault("game_b", EMPTY)
    st.session_state.setdefault("game_b_history", [])
    st.session_state.setdefault("game_answer", "")
    st.session_state.setdefault("game_report_submitted", False)
    st.session_state.setdefault("game_a_feedback", "")
    st.session_state.setdefault("game_b_feedback", "")


initialize_session()
st.title("쌓기나무 탐정단: 같은 사진, 다른 건물")
tab_search, tab_make, tab_game = st.tabs([
    "그림으로 3D 모형 찾기",
    "나만의 쌓기나무 만들기",
    "탐정 게임: 같은 사진, 다른 건물",
])
with tab_search:
    render_search_tab()
with tab_make:
    render_make_tab()
with tab_game:
    render_game_tab()
