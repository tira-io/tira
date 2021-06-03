<script type="text/javascript">
    function reload_dom_element(id){
      $(id).load(document.URL + " " + id);
      setTimeout(reload_dom_element(id), 10000);
    };
</script>
