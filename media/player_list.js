function run_search() {
    var parms = {};
    parms['position'] = $("#search_pos").val();
    if($("#player_name").val()){
        parms['name'] = $("#player_name").val();
    }
    window.location = setURLVars(parms);
}

$(document).ready(function(){
    $("#run_filter").click(function(){
        run_search();
    });
    $("#player_name").keyup(function(e){
        var code = (e.keyCode ? e.keyCode : e.which);
        if(code == 13){
            run_search();
        }
    });
});
