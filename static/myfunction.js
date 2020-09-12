function myFunction(my_element, result_element) {
    if( /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ) {

    }

    if ($(window).width() < 992) {
        $([document.documentElement, document.body]).animate({
            scrollTop: $("#" + my_element).offset().top-20
        }, 500);
        $(".jumbotron").height(2000);
    }

    var searched_text = document.getElementById(my_element).value;
    if(searched_text.length > 1) {
        fetch("/api/search?misto=" + searched_text)
            .then(function (response) {
            //$('#dropdown-menu').fadeOut(50);

                return response.json();

            })
            .then(function (myJson) {
                console.log(myJson);
                var i = 0;
                var obj = JSON.parse(myJson);

                // we create an element


                document.getElementById(result_element).innerHTML = "";
                // TODO: Dokončit vyhledávání stisknutím enteru, v tuto chvíli neočekávan chování, při stisknutí entru to hodí default stránku

                $('#'+ my_element).on('keypress', function (e) {
                 if(e.which === 13) {
                    $(my_element).submit(function(e){
                        e.preventDefault();
                    });

                     if ($(document.querySelector("#" + result_element + "> a")).length >= 1) {
                         $(document.querySelector("#" + result_element + "> a")).click()
                     } else
                     {

                     }

                 }
                });
                while(i < obj.length)
                {
                    // jen kraj
                    if (obj[i]["ID_OBECMESTO"] == null && obj[i]["ID_NUTS"] == null && obj[i]["ID_OKRES"] == null)
                    {
                        var params = '/opatreni/?kraj_id=replace'.replace("replace",  obj[i]["ID_KRAJ"]);

                        var button = "<a type='button' class='btn  btn-block btn-dark cut-text'  href='"+params+"'><span style='color:lightgray'>kraj_str</span></div></a>";
                        button = button.replace("parametry", params);
                        button = button.replace("kraj_str", obj[i]["NAZEV_KRAJ"]);
                        document.getElementById(result_element).innerHTML += button;
                    // OKRES + kraj
                    } else if (obj[i]["ID_OBECMESTO"] == null && obj[i]["ID_NUTS"] == null && obj[i]["ID_OKRES"] != null && obj[i]["ID_KRAJ"] != null)
                    {
                        var params = '/opatreni/?okres_id=replace'.replace("replace",  obj[i]["ID_OKRES"]);

                        var button = "<a type='button' class='btn  btn-block btn-dark cut-text'  href='"+params+"'>okres_str<span style='color:lightgray'>, kraj_str</span></div></a>";
                        button = button.replace("parametry", params);
                        button = button.replace("okres_str", obj[i]["NAZEV_OKRES"]);
                        button = button.replace("kraj_str", obj[i]["NAZEV_KRAJ"]);
                        document.getElementById(result_element).innerHTML += button;

                    }
                    // nuts + kraj
                    else if (obj[i]["ID_OBECMESTO"] == null && obj[i]["ID_NUTS"] != null && obj[i]["ID_OKRES"] != null && obj[i]["ID_KRAJ"] != null)
                    {
                        var params = '/opatreni/?nuts3_id=replace'.replace("replace", obj[i]["ID_NUTS"]);

                        var button = "<a type='button' class='btn  btn-block btn-secondary cut-text'  href='"+params+"'>nuts3_str<span style='color:lightgray'>, okres_str, kraj_str</span></div></a>";
                        button = button.replace("parametry", params);
                        button = button.replace("okres_str", obj[i]["NAZEV_OKRES"]);

                        button = button.replace("nuts3_str", obj[i]["NAZEV_NUTS"]);
                        button = button.replace("kraj_str", obj[i]["NAZEV_KRAJ"]);
                        document.getElementById(result_element).innerHTML += button;
                    // obecmesto
                    }
                    else if (obj[i]["ID_OBECMESTO"] != null && obj[i]["ID_NUTS"] != null && obj[i]["ID_OKRES"] != null && obj[i]["ID_KRAJ"] != null)
                    {
                        //         SELECT  null as id_obecmesto, null as nazev_obecmesto, null as id_nuts, null as nazev_nuts, nazev_kraj, id_kraj from kraj WHERE nazev_kraj LIKE '%Pra%'

                         var params = '/opatreni/?obecmesto_id=replace'.replace("replace",  obj[i]["ID_OBECMESTO"]);

                        var button = "<a type='button' class='btn  btn-block btn-secondary cut-text'    href='"+params+"'>obecmesto_str<span style='color:lightgray'>, okres_str, kraj_str</span></div></a>";
                        button = button.replace("parametry", params);
                        button = button.replace("obecmesto_str", obj[i]["NAZEV_OBECMESTO"]);
                        button = button.replace("okres_str", obj[i]["NAZEV_OKRES"]);

                        button = button.replace("kraj_str", obj[i]["NAZEV_KRAJ"]);
                        document.getElementById(result_element).innerHTML += button;
                    }
                    i = i + 1;
                }
                if(obj.length == 0) // spapny vstup, neni v databazi
                {
                    document.getElementById(result_element).innerHTML = '<div class="alert alert-dark"><strong>Nenalezeno!</strong>\nZkuste název napsat znovu. Pokud ani to nepomůže, vyberte místo v okolí. Vyhledávat můžete podle kraje, okresu, obce s rozšířenou působností, města, či obce.</div>'
                }
                //$('#dropdown-menu').hide().fadeIn(50);

                })


            .catch(function (error) {
                console.log("Error: " + error);
            });
    }
}
