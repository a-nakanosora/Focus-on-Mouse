# Focus on Mouse
ビューの中心点をマウス下のオブジェクト上の一点に合わせます。

![image](https://raw.githubusercontent.com/wiki/a-nakanosora/blender-scripts/images/bl-focus-on-mouse/behivor.gif)

<br>

## Installation

Blender User Preferences > Install from File にて `view3d_focus_on_mouse.py` を選択。
ホットキー設定で`Focus on Mouse`が有効になります。
デフォルトでは`Shift+Ctrl+Q`キーに割り当てられます。

<br>

## Center View to Mouse との違い
Blenderに標準で用意されている似た機能に`Center View to Mouse`があります。

![image](https://raw.githubusercontent.com/wiki/a-nakanosora/blender-scripts/images/bl-focus-on-mouse/hotkey.png)

マウス下の点に中心点を合わせるという点でこれとFocus on Mouse は本質的には同等の働きを担いますが、
中心点を合わせる際の挙動としてビューの位置と回転の扱いが異なっています。

![image](https://raw.githubusercontent.com/wiki/a-nakanosora/blender-scripts/images/bl-focus-on-mouse/difference.gif)

Focus on Mouse はビューの位置を変えずにアングルだけ変えるので、部分的に`Fly Mode`に似た挙動となっています。
広い建造物といった、遠くと近くとで奥行きが大きく異なるオブジェクト上でのビューの中心点の制御は`Center View to Mouse`だと
挙動がピーキーになりやすいので、その時は`Focus on Mouse`を使ったほうがいいと思います。
