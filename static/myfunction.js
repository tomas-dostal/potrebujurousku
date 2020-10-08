function myFunction(my_element, result_element) {
    if( /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {

    }


    $([document.documentElement, document.body]).animate({
        scrollTop: $("#" + my_element).offset().top-50
    }, 1000);


    var searched_text = document.getElementById(my_element).value;
    if(searched_text.length > 2) {
        fetch("/api/search?misto=" + searched_text)
            .then(function (response) {
            //$('#dropdown-menu').fadeOut(50);
                $('#spinner').css('visibility', 'visible');
                return response.json();

            })
            .then(function (myJson) {
                //console.log(myJson);
                var i = 0;
                var obj = JSON.parse(myJson);

                // we create an element

                $('#spinner').css('visibility', 'hidden');

                document.getElementById(result_element).innerHTML = "";
                // TODO: Dokončit vyhledávání stisknutím enteru, v tuto chvíli neočekávan chování, při stisknutí entru to hodí default stránku

                $('#'+ my_element).on('keypress', function (e) {
                    if (e.which === 13) {
                        $(my_element).submit(function (e) {
                            e.preventDefault();
                        });
                        var selector = "#" + result_element + " a";

                        $(document).ready(function () {
                            if ($(document.querySelector('' + selector)).length >= 1) {
                                $('' + selector)[0].click();
                            } else {
                            }

                        });
                    }
                });

                while(i < obj.length)
                {


                    // jen kraj
                    if (obj[i]["ID_OBECMESTO"] == null && obj[i]["ID_NUTS"] == null && obj[i]["ID_OKRES"] == null)
                    {
                        var params = '/opatreni/?kraj_id=replace'.replace("replace",  obj[i]["ID_KRAJ"]);

                        card = "<div class=\"card  text-white bg-dark \" id=\"obecmesto-obecmesto_id\"style=\"max-width: 18rem;\">\n" +
                            "              <div class=\"card-header h3\">kraj_str</div>\n" +
                            "              <div class=\"card-body\">\n" +
                           // "                <h5 class=\"card-title\">Secondary card title</h5>\n" +
                            "            <p class=\"card-text\"></p><a href=\"parametry\" class=\"btn btn-primary stretched-link\">Zvolit místo</a>\n" +
                            "          </div>\n" +
                            "        </div>";
                        card = card.replace("kraj_id", obj[i]["ID_KRAJ"]);
                        card = card.replace("parametry", params);
                        card = card.replace("kraj_str", obj[i]["NAZEV_KRAJ"]);
                        document.getElementById(result_element).innerHTML += card;
                    // OKRES + kraj
                    } else if (obj[i]["ID_OBECMESTO"] == null && obj[i]["ID_NUTS"] == null && obj[i]["ID_OKRES"] != null && obj[i]["ID_KRAJ"] != null)
                    {
                        var params = '/opatreni/?okres_id=replace'.replace("replace",  obj[i]["ID_OKRES"]);

                        card = "<div class=\"card  text-white bg-secondary \" id=\"obecmesto-obecmesto_id\"style=\"max-width: 18rem;\">\n" +
                            "              <div class=\"card-header h3\">okres_str</div>\n" +
                            "              <div class=\"card-body\">\n" +
                            "                <h5 class=\"card-title\">kraj_str</h5>\n" +
                            "            <p class=\"card-text\"></p><a href=\"parametry\" class=\"btn btn-primary stretched-link\">Zvolit místo</a>\n" +
                            "          </div>\n" +
                            "        </div>";
                        card = card.replace("okres_id", obj[i]["ID_OKRES"]);
                        card = card.replace("parametry", params);
                        card = card.replace("okres_str", obj[i]["NAZEV_OKRES"]);
                        card = card.replace("kraj_str", obj[i]["NAZEV_KRAJ"]);
                        document.getElementById(result_element).innerHTML += card;

                    }
                    // nuts + kraj
                    else if (obj[i]["ID_OBECMESTO"] == null && obj[i]["ID_NUTS"] != null && obj[i]["ID_OKRES"] != null && obj[i]["ID_KRAJ"] != null)
                    {
                        var params = '/opatreni/?nuts3_id=replace'.replace("replace", obj[i]["ID_NUTS"]);

                        card = "<div class=\"card  bg-light \" id=\"obecmesto-obecmesto_id\"style=\"max-width: 18rem;\">\n" +
                            "              <div class=\"card-header h3\">nuts3_str</div>\n" +
                            "              <div class=\"card-body\">\n" +
                            "                <h5 class=\"card-title\">okres_str, kraj_str</h5>\n" +
                            "            <p class=\"card-text\"></p><a href=\"parametry\" class=\"btn btn-primary stretched-link\">Zvolit místo</a>\n" +
                            "          </div>\n" +
                            "        </div>";
                        card = card.replace("nuts_id", obj[i]["ID_NUTS"]);
                        card = card.replace("parametry", params);
                        card = card.replace("okres_str", obj[i]["NAZEV_OKRES"]);

                        card = card.replace("nuts3_str", obj[i]["NAZEV_NUTS"]);
                        card = card.replace("kraj_str", obj[i]["NAZEV_KRAJ"]);
                        document.getElementById(result_element).innerHTML += card;
                    // obecmesto
                    }
                    else if (obj[i]["ID_OBECMESTO"] != null && obj[i]["ID_NUTS"] != null && obj[i]["ID_OKRES"] != null && obj[i]["ID_KRAJ"] != null)
                    {
                        //         SELECT  null as id_obecmesto, null as nazev_obecmesto, null as id_nuts, null as nazev_nuts, nazev_kraj, id_kraj from kraj WHERE nazev_kraj LIKE '%Pra%'

                         var params = '/opatreni/?obecmesto_id=replace'.replace("replace",  obj[i]["ID_OBECMESTO"]);

                        card = "<div class=\"card  bg-light \" id=\"obecmesto-obecmesto_id\"style=\"max-width: 18rem;\">\n" +
                                    "              <div class=\"card-header h3\">obecmesto_str</div>\n" +
                                    "              <div class=\"card-body\">\n" +
                                    "                <h5 class=\"card-title\">okres_str, kraj_str</h5>\n" +
                                    "            <p class=\"card-text\">Správní celek nuts_str" +
                                    "</p><a href=\"parametry\" class=\"btn btn-primary stretched-link\">Zvolit místo</a>\n" +
                                    "          </div>\n" +
                                    "        </div>";
                        card = card.replace("parametry", params);
                        card = card.replace("obecmesto_id", obj[i]["ID_OBECMESTO"]);
                        card = card.replace("obecmesto_str", obj[i]["NAZEV_OBECMESTO"]);
                        card = card.replace("okres_str", obj[i]["NAZEV_OKRES"]);
                        card = card.replace("nuts_str",  obj[i]["NAZEV_NUTS"]);
                        card = card.replace("kraj_str", obj[i]["NAZEV_KRAJ"]);
                        document.getElementById(result_element).innerHTML += card;
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
    else
    {
        document.getElementById(result_element).innerHTML = "";
    }
}
