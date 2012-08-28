$(document).ready(function(){
    $("#run_filter").click(function(){
        var parms = {};
        var search_pos = $("#search_pos");
        parms['position'] = search_pos.val();
        window.location = setURLVars(parms);
    });
});
