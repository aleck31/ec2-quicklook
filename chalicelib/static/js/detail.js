console.log('Loading modular detail.js...');

new Vue({
  el: '#app',
  delimiters: ['[[', ']]'],
  
  data: {
    region: document.getElementById('region').value,
    type: document.getElementById('type').value,
    instanceDetail: null,
    loading: true
  },

  mounted() {
    console.log('Vue instance mounted');
    console.log('Region:', this.region);
    console.log('Type:', this.type);
    this.loadInstanceDetail();
  },

  methods: {
    async loadInstanceDetail() {
      try {
        console.log('Loading instance detail...');
        this.loading = true;
        const response = await axios.get('/instance/detail', {
          params: {
            region: this.region,
            type: this.type
          }
        });
        console.log('Response:', response.data);
        this.instanceDetail = response.data;
      } catch (error) {
        console.error('Error loading instance detail:', error);
        this.instanceDetail = null;
      } finally {
        this.loading = false;
      }
    }
  }
});
