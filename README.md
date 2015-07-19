DanTube
=======
Code danmaku basic example:
var pos_x = 0;
create_danmaku('sss', function(ele, delta) {
    var speed = (100*danmaku_speed + 400)/10;
    if (pos_x > player_width + ele.offsetWidth) {
        return true;
    } else {
        pos_x += speed*delta;
        ele.style.WebkitTransform = "translate(-"+pos_x+"px, 0px)";
        ele.style.msTransform = "translate(-"+pos_x+"px, 0px)";
        ele.style.transform = "translate(-"+pos_x+"px, 0px)";
        return false;
    }
});